import { render, screen, waitFor, within, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import App from "../App";
import diwali from "./fixtures/diwali.json";

const OCCASIONS = {
  occasions: [
    { name: "Birthday", featured: true },
    { name: "Diwali", featured: true },
    { name: "Wedding", featured: true },
  ],
};
const EMPTY = { query: "xqzvw", resolved_occasion: null, total: 0, returned: 0, results: [] };
const ok = (body) => Promise.resolve({ ok: true, status: 200, json: async () => body });

/** Routes fetch calls the way the real API would. `failFirst` makes the first recommendations call fail. */
function mockApi({ failFirst = false } = {}) {
  let failed = false;
  const fetchMock = vi.fn((url) => {
    const u = new URL(url, "http://test");
    if (u.pathname === "/api/occasions") return ok(OCCASIONS);
    const q = u.searchParams.get("occasion");
    if (failFirst && !failed) {
      failed = true;
      return Promise.reject(new TypeError("network down"));
    }
    if (q?.toLowerCase() === "diwali") return ok(diwali);
    return ok({ ...EMPTY, query: q });
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

beforeEach(() => {
  window.history.replaceState(null, "", "/");
  vi.unstubAllGlobals();
});

describe("Occasion recommender UI", () => {
  it("shows a labelled occasion input and an action button before any search", async () => {
    mockApi();
    render(<App />);
    expect(screen.getByLabelText("Occasion")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Find gifts" })).toBeInTheDocument();
    expect(await screen.findByRole("button", { name: "Diwali" })).toBeInTheDocument(); // chips from the API
  });

  it("renders ranked product cards below the input, on the same page", async () => {
    mockApi();
    render(<App />);
    await userEvent.type(screen.getByLabelText("Occasion"), "Diwali");
    await userEvent.click(screen.getByRole("button", { name: "Find gifts" }));

    const first = diwali.results[0];
    const card = (await screen.findByRole("heading", { name: first.title })).closest("article");
    expect(within(card).getByText(first.vendor_category_desc)).toBeInTheDocument(); // category
    expect(within(card).getByText(first.snippet)).toBeInTheDocument();              // description snippet
    expect(within(card).getByRole("img", { name: first.title })).toHaveAttribute("src", first.image); // image
    expect(within(card).getByRole("meter", { name: "Match strength" })).toBeInTheDocument();
    expect(screen.getByLabelText("Occasion")).toHaveValue("Diwali");                 // input still there
    expect(screen.getAllByRole("article")).toHaveLength(diwali.results.length);
    expect(screen.getByRole("heading", { name: /Gifts for Diwali/ })).toBeInTheDocument();
  });

  it("searches in real time after the person pauses typing", async () => {
    const fetchMock = mockApi();
    render(<App />);
    await userEvent.type(screen.getByLabelText("Occasion"), "Diwali");
    expect(await screen.findByRole("heading", { name: diwali.results[0].title }, { timeout: 3000 })).toBeInTheDocument();
    expect(fetchMock.mock.calls.filter(([u]) => u.includes("/api/recommendations"))).toHaveLength(1); // debounced
  });

  it("runs a search when a suggestion chip is clicked", async () => {
    mockApi();
    render(<App />);
    await userEvent.click(await screen.findByRole("button", { name: "Diwali" }));
    expect(await screen.findByRole("heading", { name: diwali.results[0].title })).toBeInTheDocument();
    expect(screen.getByLabelText("Occasion")).toHaveValue("Diwali");
  });

  it("shows an empty state with next steps when nothing matches", async () => {
    mockApi();
    render(<App />);
    await userEvent.type(screen.getByLabelText("Occasion"), "xqzvw{Enter}");
    expect(await screen.findByText(/Nothing in the catalog fits/)).toBeInTheDocument();
    expect(screen.queryAllByRole("article")).toHaveLength(0);
    expect(screen.getAllByRole("button", { name: "Birthday" }).length).toBeGreaterThan(0);
  });

  it("explains failures and recovers on retry", async () => {
    mockApi({ failFirst: true });
    render(<App />);
    await userEvent.type(screen.getByLabelText("Occasion"), "Diwali{Enter}");
    expect(await screen.findByRole("alert")).toHaveTextContent(/couldn.t load recommendations/i);
    await userEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(await screen.findByRole("heading", { name: diwali.results[0].title })).toBeInTheDocument();
  });

  it("falls back to a placeholder when a product image fails to load", async () => {
    mockApi();
    render(<App />);
    await userEvent.click(await screen.findByRole("button", { name: "Diwali" }));
    const first = diwali.results[0];
    const img = await screen.findByRole("img", { name: first.title });
    fireEvent.error(img);
    expect(await screen.findByRole("img", { name: `${first.title} (no image available)` })).toBeInTheDocument();
  });

  it("restores the search from the URL", async () => {
    window.history.replaceState(null, "", "/?occasion=Diwali");
    mockApi();
    render(<App />);
    expect(screen.getByLabelText("Occasion")).toHaveValue("Diwali");
    await waitFor(() => expect(screen.getAllByRole("article").length).toBeGreaterThan(0));
  });
});
