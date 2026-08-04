export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    let pathname = url.pathname;
    if (pathname === "/" || pathname.endsWith("/")) {
      pathname += "index.html";
    }
    url.pathname = pathname;
    return env.ASSETS.fetch(new Request(url, request));
  }
}
