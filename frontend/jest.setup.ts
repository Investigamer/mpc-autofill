// The below can be used in a Jest global setup file or similar for your testing set-up
import { loadEnvConfig } from "@next/env";
import "@testing-library/jest-dom";
import { server } from "@/mocks/server";
// Polyfill "window.fetch" used in the React component.
import "whatwg-fetch";

// retrieved from https://stackoverflow.com/a/68539103/13021511
global.matchMedia =
  global.matchMedia ||
  function () {
    return {
      matches: false,
      addListener: function () {},
      removeListener: function () {},
    };
  };

export default async () => {
  const projectDir = process.cwd();
  loadEnvConfig(projectDir);
};
//
// Establish API mocking before all tests.
beforeAll(() => server.listen());

// Reset any request handlers that we may add during the tests,
// so they don't affect other tests.
afterEach(() => server.resetHandlers());

// Clean up after the tests are finished.
afterAll(() => server.close());
