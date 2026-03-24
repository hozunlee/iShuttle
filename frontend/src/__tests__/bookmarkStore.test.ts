/**
 * FE_004 — bookmarkStore 테스트
 * - toggle: 북마크 추가/제거
 * - isBookmarked: 상태 확인
 * - count: 개수
 * - clear: 전체 초기화
 * - Set 직렬화 (localStorage 저장/복원)
 */
import { describe, it, expect, beforeEach } from "vitest";
import { useBookmarkStore } from "../store/bookmarkStore";

describe("bookmarkStore", () => {
  beforeEach(() => {
    useBookmarkStore.getState().clear();
  });

  it("초기 상태: 북마크 없음", () => {
    expect(useBookmarkStore.getState().count()).toBe(0);
  });

  it("toggle: 없던 ID 추가", () => {
    useBookmarkStore.getState().toggle(1);
    expect(useBookmarkStore.getState().isBookmarked(1)).toBe(true);
    expect(useBookmarkStore.getState().count()).toBe(1);
  });

  it("toggle: 있던 ID 제거", () => {
    useBookmarkStore.getState().toggle(1);
    useBookmarkStore.getState().toggle(1);
    expect(useBookmarkStore.getState().isBookmarked(1)).toBe(false);
    expect(useBookmarkStore.getState().count()).toBe(0);
  });

  it("여러 ID 독립적으로 관리", () => {
    useBookmarkStore.getState().toggle(1);
    useBookmarkStore.getState().toggle(2);
    useBookmarkStore.getState().toggle(3);
    expect(useBookmarkStore.getState().count()).toBe(3);
    expect(useBookmarkStore.getState().isBookmarked(2)).toBe(true);
  });

  it("toggle 2번 = 원상복귀 (idempotent)", () => {
    useBookmarkStore.getState().toggle(5);
    useBookmarkStore.getState().toggle(5);
    expect(useBookmarkStore.getState().isBookmarked(5)).toBe(false);
  });

  it("clear: 전체 초기화", () => {
    useBookmarkStore.getState().toggle(1);
    useBookmarkStore.getState().toggle(2);
    useBookmarkStore.getState().clear();
    expect(useBookmarkStore.getState().count()).toBe(0);
    expect(useBookmarkStore.getState().isBookmarked(1)).toBe(false);
  });

  it("isBookmarked: 없는 ID → false", () => {
    expect(useBookmarkStore.getState().isBookmarked(999)).toBe(false);
  });

  it("count: 정확한 개수 반환", () => {
    [10, 20, 30, 40].forEach((id) => useBookmarkStore.getState().toggle(id));
    expect(useBookmarkStore.getState().count()).toBe(4);
    useBookmarkStore.getState().toggle(10); // 제거
    expect(useBookmarkStore.getState().count()).toBe(3);
  });
});
