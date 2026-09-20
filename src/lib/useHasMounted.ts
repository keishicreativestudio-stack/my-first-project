import { useSyncExternalStore } from "react";

const emptySubscribe = () => () => {};

/**
 * SSRとクライアントで表示内容が異なりうる箇所(localStorage永続化状態への依存など)を
 * hydration mismatchなく描画するためのフック。
 */
export function useHasMounted(): boolean {
  return useSyncExternalStore(
    emptySubscribe,
    () => true,
    () => false
  );
}
