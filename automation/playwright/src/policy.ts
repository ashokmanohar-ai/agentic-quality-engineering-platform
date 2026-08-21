export const allowedGeneratedRoot = new URL("../generated/", import.meta.url);

export function assertSafeGeneratedPath(relativePath: string): URL {
  if (!/^[a-z0-9-]+\.spec\.ts$/i.test(relativePath)) {
    throw new Error("Unsafe generated test path");
  }
  const destination = new URL(relativePath, allowedGeneratedRoot);
  if (!destination.href.startsWith(allowedGeneratedRoot.href)) {
    throw new Error("Generated path escaped the approved workspace");
  }
  return destination;
}
