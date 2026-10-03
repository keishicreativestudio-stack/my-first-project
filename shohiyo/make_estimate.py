"""販売図面から読み取った物件情報（JSON）をもとに、資金計算書（概算）の Excel を作る。

使い方:
    python3 shohiyo/make_estimate.py 物件.json [出力.xlsx]

JSON の項目は README.md を参照。概算値（登記費用・火災保険など）は ESTIMATES の
ルールで自動設定し、JSON の "overrides" で個別に上書きできる。
"""
import datetime
import json
import re
import sys
import warnings
import zipfile
from pathlib import Path

from openpyxl import Workbook
from openpyxl.comments import Comment
from openpyxl.styles import Alignment, Border, Font, Side

sys.path.insert(0, str(Path(__file__).resolve().parent))
from reds_fee import reds_fee  # noqa: E402

TYPES = ('新築戸建', '中古戸建', '新築マンション', '中古マンション', '土地')
DEALS = ('仲介', '売主', '代理')
FEE_PLANS = ('割引', '無料', '半額')
OTHER_AGENT_ADMIN_FEE = 55000  # 他社の事務代行手数料（税込）
BANK_FEE_RATE = 0.022  # 融資事務手数料（融資額 × 2.2%）

FONT = '游ゴシック'
YEN = '"¥"#,##0;[Red]"¥"\\-#,##0'
RED = 'FFFF0000'
BLUE = 'FF0000FF'
thin = Side(style='thin', color='FF999999')


# ---- 概算ルール（図面からは分からない費用） -------------------------------------

def estimate_registration(price, kind):
    """登記費用（移転・保存・抵当権設定＋司法書士報酬）の概算。物件価格帯で決める。"""
    brackets = [(20000000, 250000), (30000000, 300000), (40000000, 350000),
                (50000000, 400000), (60000000, 450000), (80000000, 500000),
                (100000000, 600000)]
    fee = next((v for limit, v in brackets if price <= limit), 700000)
    return fee - 50000 if kind == '土地' else fee  # 土地は建物の登記がない


def estimate_fire_insurance(kind):
    """火災保険（5年・地震保険込）の概算。"""
    return {'土地': 0, '新築マンション': 200000, '中古マンション': 200000}.get(kind, 350000)


def estimate_property_tax(kind):
    """固定資産税・都市計画税の日割清算金の概算。"""
    return {'土地': 50000, '新築マンション': 50000, '中古マンション': 80000}.get(kind, 100000)


def is_old_seismic(built_year):
    """旧耐震（1981年5月以前の建築確認）の可能性があるか。築年のみで判定する。"""
    return built_year is not None and built_year <= 1981


# ---- 物件情報の検証・既定値 ---------------------------------------------------

def normalize(spec):
    s = dict(spec)
    if s.get('type') not in TYPES:
        raise ValueError(f"type は {TYPES} のいずれか: {s.get('type')!r}")
    if s.get('deal', '仲介') not in DEALS:
        raise ValueError(f"deal は {DEALS} のいずれか: {s.get('deal')!r}")
    s['deal'] = s.get('deal', '仲介')
    s['price'] = int(s['price'])
    s.setdefault('fee_plan', '割引')
    if s['fee_plan'] not in FEE_PLANS:
        raise ValueError(f"fee_plan は {FEE_PLANS} のいずれか: {s['fee_plan']!r}")
    loan = {'amount': None, 'rate': 0.945, 'years': 35, 'bonus': 0,
            'bank': '（仮）都市銀行', 'rate_type': '変動金利'}
    loan.update(s.get('loan') or {})
    if loan['amount'] is None:
        loan['amount'] = s['price']  # 既定: 物件価格を全額借入、諸費用は自己資金
    s['loan'] = loan
    s.setdefault('overrides', {})
    return s


def build_items(s):
    """諸経費の行リスト。各行: (項目名, 説明, REDS側の値/式, 他社側の値/式, 約をつけるか, 根拠コメント)"""
    price, kind, ov = s['price'], s['type'], s['overrides']
    items = []

    def val(key, default):
        return ov.get(key, default)

    items.append(('契約書印紙代',
                  '（売買契約書の印紙税。軽減税率：1千万超5千万以下1万円、5千万超1億以下3万円、1億超5億以下6万円）',
                  '=LOOKUP(E8-1,{0,500000,1000000,5000000,10000000,50000000,100000000,500000000},'
                  '{200,500,1000,5000,10000,30000,60000,160000})',
                  '=E@ROW@', False, '印紙税法 別表第一 第1号文書・租税特別措置法の軽減税率（2027年3月31日まで）'))

    legal = '=INT(IF(E8<=2000000,INT(E8*0.05),IF(E8<=4000000,INT(100000+(E8-2000000)*0.04),INT(E8*0.03+60000)))*1.1)'
    if s['deal'] in ('売主', '代理'):
        items.append(('仲介手数料（不要）', f"（取引態様が「{s['deal']}」のため仲介手数料はかかりません）",
                      0, 0, False, None))
    else:
        plan = s['fee_plan']
        if plan == '無料':
            reds = 0
            note = None
        elif plan == '半額':
            reds = '=INT(H@ROW@/2)'
            note = '他社（法定上限）の半額'
        else:
            r = reds_fee(price)
            reds = r['fee_and_tax']
            note = (f"REDS手数料計算（calc10_2）で算出: ({r['rate']}%＋3万円)×1.1"
                    + (f"、上限 {r['limit_str']}" if r['limit_str'] else '')
                    + f"／割引率 {r['discount_rate']}%")
        items.append((f'仲介手数料（{plan}）', '（一般的な仲介手数料は、物件価格の3％＋6万円に消費税）',
                      val('仲介手数料', reds), legal, False, note))
        items.append(('事務代行手数料', '（契約書類作成、物件調査、住宅ローン等の代行手数料　約5～10万円）',
                      0, OTHER_AGENT_ADMIN_FEE, True, None))

    items.append(('登記費用', '（移転登記・保存登記・抵当権設定の登録免許税と司法書士報酬）',
                  val('登記費用', estimate_registration(price, kind)), '=E@ROW@', True,
                  '概算（物件価格帯による目安）。固定資産税評価額が分かれば司法書士見積で差し替え'))
    if kind != '土地':
        items.append(('火災保険', '（火災保険5年加入・地震保険込の目安）',
                      val('火災保険', estimate_fire_insurance(kind)), '=E@ROW@', True, '概算（目安）'))
    items.append(('固定資産税・都市計画税清算金', '（固定資産税・都市計画税の年間支払額を引渡日で日割清算します）',
                  val('固定資産税・都市計画税清算金', estimate_property_tax(kind)), '=E@ROW@', True,
                  '概算（目安）。年税額が分かれば日割で差し替え'))
    if kind == '新築戸建':
        items.append(('表示登記費用', '（建物表題登記。土地家屋調査士に支払います）',
                      val('表示登記費用', 150000), '=E@ROW@', True, '概算（目安）'))
    if kind.endswith('マンション'):
        monthly = (s.get('management_fee') or 0) + (s.get('repair_reserve') or 0)
        items.append(('管理費・修繕積立金清算金', '（管理費・修繕積立金の日割清算。約2ヶ月分）',
                      val('管理費・修繕積立金清算金', monthly * 2 if monthly else 60000), '=E@ROW@', True,
                      f"図面の管理費＋修繕積立金 月額{monthly:,}円 × 2ヶ月" if monthly else '概算（図面に記載なし）'))
    if kind == '新築マンション' and s.get('initial_repair_fund'):
        items.append(('修繕積立基金', '（新築時に一括で支払う修繕積立基金）',
                      s['initial_repair_fund'], '=E@ROW@', False, '販売図面記載額'))
    items.append(('融資事務手数料', '（銀行に支払う融資手数料です。融資額×2.2％）',
                  f'=INT(E@LOAN@*{BANK_FEE_RATE})', '=E@ROW@', True, '融資事務手数料型（定率2.2%）の場合'))
    items.append(('金銭消費貸借契約書印紙代', '（銀行との金銭消費貸借契約書に貼付する収入印紙。WEB契約の場合は無料）',
                  '=IF(E@LOAN@<=0,0,LOOKUP(E@LOAN@-1,{0,100000,500000,1000000,5000000,10000000,50000000,100000000},'
                  '{200,400,1000,2000,10000,20000,60000,100000}))',
                  '=E@ROW@', False, '印紙税法 別表第一 第1号文書（消費貸借契約書）'))
    return items


# ---- Excel 出力 --------------------------------------------------------------

def write_workbook(s, out_path):
    wb = Workbook()
    ws = wb.active
    ws.title = '資金計算書'
    for col, w in {'A': 12, 'B': 16, 'C': 23, 'D': 5, 'E': 22, 'F': 3, 'G': 5, 'H': 18}.items():
        ws.column_dimensions[col].width = w

    def put(ref, value, size=12, bold=False, color=None, fmt=None, align=None, wrap=False):
        c = ws[ref]
        c.value = value
        c.font = Font(name=FONT, size=size, bold=bold, color=color)
        if fmt:
            c.number_format = fmt
        if align or wrap:
            c.alignment = Alignment(horizontal=align, vertical='center', wrap_text=wrap)
        return c

    # 見出し
    ws.merge_cells('A1:B2')
    put('A1', f"{s.get('customer', '')}　様", 16, True, align='center')
    ws.merge_cells('C1:E2')
    put('C1', '資金計算書（概算）', 16, True, align='center')
    ws.merge_cells('F1:H1')
    put('F1', '=TODAY()', 10, True, fmt='[$-411]ggge"年"m"月"d"日";@', align='center')
    ws.merge_cells('F2:H2')
    put('F2', '株式会社不動産流通システム', 10, True, align='center')
    ws.merge_cells('F3:H3')
    put('F3', f"担当：{s.get('staff', '')}", 10, True, align='center')

    put('A4', '物件名', bold=True)
    ws.merge_cells('B4:H4')
    put('B4', s.get('name', ''), align='left')
    put('A5', '物件所在地', bold=True)
    ws.merge_cells('B5:H5')
    put('B5', s.get('address', ''), align='left')
    put('A6', '種別', bold=True)
    ws.merge_cells('B6:H6')
    extra = '　旧耐震の可能性あり' if is_old_seismic(s.get('built_year')) else ''
    built = f"　築{s['built_year']}年" if s.get('built_year') else ''
    put('B6', f"{s['type']}　取引態様：{s['deal']}{built}{extra}", align='left')

    put('A8', '物件価格', bold=True)
    put('C8', '売買代金', 12, align='right')
    put('E8', s['price'], 14, True, BLUE, YEN, 'right')
    put('C10', '小計', 12, align='right')
    put('E10', '=E8', 14, True, fmt=YEN, align='right')

    put('A13', '諸経費', bold=True)
    put('E13', 'REDSの場合', bold=True, align='center')
    put('H13', '他社の場合', bold=True, align='center')

    items = build_items(s)
    first = row = 14
    # 融資金額のセル位置は諸経費の行数で決まるので先に計算する
    sub_row = first + len(items) * 2
    total_row, diff_row = sub_row + 2, sub_row + 4
    own_row, loan_row = sub_row + 6, sub_row + 8
    for name, desc, reds, other, approx, note in items:
        fill = lambda v: v.replace('@ROW@', str(row)).replace('@LOAN@', str(loan_row)) if isinstance(v, str) else v
        ws.merge_cells(f'B{row}:C{row}')
        put(f'B{row}', name, 14, True)
        if approx:
            put(f'D{row}', '約', 12, align='right')
            put(f'G{row}', '約', 12, align='right')
        is_fee = name.startswith('仲介手数料')
        reds_val, other_val = fill(reds), fill(other)
        e = put(f'E{row}', reds_val, 14, True, RED if is_fee else (BLUE if not isinstance(reds, str) else None),
                YEN, 'right')
        put(f'H{row}', other_val, 14, True, RED if is_fee else None, YEN, 'right')
        if note:
            e.comment = Comment(note, 'shohiyo')
        ws.merge_cells(f'B{row + 1}:H{row + 1}')
        put(f'B{row + 1}', desc, 10)
        row += 2

    put(f'C{sub_row}', '小計', 12, align='right')
    put(f'E{sub_row}', f'=SUM(E{first}:E{sub_row - 1})', 14, True, fmt=YEN, align='right')
    put(f'H{sub_row}', f'=SUM(H{first}:H{sub_row - 1})', 14, True, fmt=YEN, align='right')
    for col in 'BCDEFGH':
        ws[f'{col}{sub_row}'].border = Border(top=thin)

    put(f'A{total_row}', '総合計額', bold=True)
    put(f'C{total_row}', '総額', 12, align='right')
    put(f'E{total_row}', f'=E10+E{sub_row}', 14, True, fmt=YEN, align='right')
    put(f'H{total_row}', f'=E10+H{sub_row}', 14, True, fmt=YEN, align='right')
    put(f'E{diff_row}', '総額差額', 12, True, align='right')
    put(f'H{diff_row}', f'=H{total_row}-E{total_row}', 14, True, RED, YEN, 'right')

    loan = s['loan']
    put(f'A{own_row}', '自己資金', bold=True)
    put(f'C{own_row}', '（総額 − 融資金額）', 10)
    put(f'E{own_row}', f'=E{total_row}-E{loan_row}', 14, True, fmt=YEN, align='right')

    ws.merge_cells(f'A{loan_row}:B{loan_row}')
    put(f'A{loan_row}', '住宅ローン明細（融資事務手数料型）', bold=True)
    put(f'C{loan_row}', '融資金額', 12, align='right')
    c = put(f'E{loan_row}', loan['amount'], 14, True, BLUE, YEN, 'right')
    c.comment = Comment('既定は物件価格の全額借入（諸費用は自己資金）。変更すると自己資金・返済額が再計算されます', 'shohiyo')
    r = loan_row + 1
    ws.merge_cells(f'A{r}:H{r}')
    put(f'A{r}', f"{loan['bank']}：借入期間{loan['years']}年間、{loan['rate_type']}年{loan['rate']}％　元利均等返済", 11)
    ws.merge_cells(f'A{r + 1}:H{r + 1}')
    put(f'A{r + 1}', '※金利は金融機関・審査により異なります。一例です。', 10)

    h = r + 2
    for col, label in zip('BCDE', ('金融機関', '融資金額', '金利(%)', '期間(年)')):
        put(f'{col}{h}', label, 11, True, align='center')
    ws.merge_cells(f'F{h}:H{h}')
    put(f'F{h}', '月々均等のお支払い', 11, True, align='center')
    b = h + 1
    put(f'B{b}', loan['bank'].replace('（仮）', ''), 11, align='center')
    put(f'C{b}', f'=E{loan_row}', 12, True, fmt=YEN, align='right')
    put(f'D{b}', loan['rate'], 12, True, BLUE, align='center')
    put(f'E{b}', loan['years'], 12, True, BLUE, align='center')
    ws.merge_cells(f'F{b}:H{b}')
    put(f'F{b}', f'=IF(AND(C{b}>0,D{b}>0,E{b}>0),ROUNDUP(INT((C{b}*(D{b}/1200)*(1+D{b}/1200)^(E{b}*12))'
                 f'/((1+D{b}/1200)^(E{b}*12)-1)),0),"-")', 14, True, fmt=YEN, align='right')

    y = b + 2
    put(f'C{y}', '年間返済額', 12, align='right')
    put(f'D{y}', '12ヶ月', 10, align='center')
    put(f'E{y}', f'=IF(ISNUMBER(F{b}),F{b}*12,0)', 14, True, fmt=YEN, align='right')
    put(f'C{y + 1}', '月々のご返済', 12, align='right')
    put(f'E{y + 1}', f'=(E{y}-E{y + 2}*2)/12', 14, True, fmt=YEN, align='right')
    put(f'C{y + 2}', 'ボーナス加算', 12, align='right')
    put(f'D{y + 2}', '年2回', 10, align='center')
    put(f'E{y + 2}', loan['bonus'], 14, True, BLUE, YEN, 'right')

    notes = ['※当該計算書の金額は作成時での概算のものであり、実際のお支払い額と異なる場合がございます。',
             '※上記費用の他、不動産取得後に不動産取得税の納税が必要となる場合があります。納期は各都道府県により異なります。']
    if is_old_seismic(s.get('built_year')):
        notes.append('※耐震基準適合証明書の発行（費用約5～6万円）を受けると、住宅ローン減税、不動産取得税・登録免許税の'
                     '減税の適用を受けることができる場合がございます。')
    n = y + 4
    for text in notes:
        ws.merge_cells(f'A{n}:H{n}')
        put(f'A{n}', text, 9, wrap=True)
        ws.row_dimensions[n].height = 26
        n += 1

    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_setup.orientation = 'portrait'
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 1
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.print_area = f'A1:H{n - 1}'
    wb.calculation.fullCalcOnLoad = True  # Excel で開いたら必ず再計算
    wb.save(out_path)


def inject_cached_values(path):
    """数式の計算結果を xlsx に書き込む（openpyxl は計算結果を保存しないため、
    スマホのプレビュー等で空欄になるのを防ぐ）。Excel で開けば通常どおり再計算される。
    計算には formulas パッケージを使う。無ければ何もしない。"""
    try:
        import formulas
    except ImportError:
        return False
    warnings.filterwarnings('ignore')
    sol = formulas.ExcelModel().loads(str(path)).finish().calculate()
    values = {}
    for key, v in sol.items():
        ref = key.split('!')[-1]
        if ':' in ref or not hasattr(v, 'value'):
            continue
        val = v.value[0][0]
        try:
            values[ref] = float(val)
        except (TypeError, ValueError):
            continue
    with zipfile.ZipFile(path) as z:
        files = {n: z.read(n) for n in z.namelist()}
    sheet = 'xl/worksheets/sheet1.xml'
    xml = files[sheet].decode('utf-8')

    def add_value(m):
        ref, body = m.group(1), m.group(3)
        if ref not in values:
            return m.group(0)
        num = values[ref]
        text = str(int(num)) if num == int(num) else repr(num)
        return f'<c r="{ref}"{m.group(2)}>{body}<v>{text}</v></c>'

    xml = re.sub(r'<c r="([A-Z]+[0-9]+)"([^>]*)>(<f>.*?</f>)(?:<v */>|<v></v>)?</c>', add_value, xml)
    files[sheet] = xml.encode('utf-8')
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        for n, data in files.items():
            z.writestr(n, data)
    return True


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    spec = normalize(json.loads(Path(sys.argv[1]).read_text(encoding='utf-8')))
    out = sys.argv[2] if len(sys.argv) > 2 else f"資金計算書_{spec.get('name') or '物件'}_{datetime.date.today():%Y%m%d}.xlsx"
    write_workbook(spec, out)
    inject_cached_values(out)
    print(out)


if __name__ == '__main__':
    main()
