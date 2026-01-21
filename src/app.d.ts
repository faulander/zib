// See https://svelte.dev/docs/kit/types#app.d.ts
// for information about these interfaces
declare global {
  namespace App {
    interface Error {
      message: string;
    }
    // eslint-disable-next-line @typescript-eslint/no-empty-object-type
    interface Locals {
      // user?: { id: string; email: string; name?: string };
    }
    // interface PageData {}
    // interface PageState {}
    // interface Platform {}
  }
}

export {};
