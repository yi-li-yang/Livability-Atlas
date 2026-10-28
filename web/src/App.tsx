import { BaseMap } from "./features/map/BaseMap";

export function App() {
  return (
    <div className="flex h-screen flex-col">
      <header className="px-4 py-2">
        <h1 className="text-2xl font-semibold">Livability Atlas</h1>
      </header>
      <main className="min-h-0 flex-1">
        <BaseMap />
      </main>
    </div>
  );
}
