import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# URL of the sitemap to check
SITEMAP_URL = 'https://ngetest.id/sitemap.xml'  # replace with your sitemap URL

# Namespace used in the sitemap XML
NS = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}


def get_urls_from_sitemap(sitemap_url):
    """Fetch URLs from sitemap XML safely handling namespace."""
    response = requests.get(sitemap_url)
    if response.status_code != 200:
        print(f"Failed to fetch sitemap: {response.status_code}")
        return []

    root = ET.fromstring(response.content)
    urls = []
    for url in root.findall('ns:url', NS):
        loc = url.find('ns:loc', NS)
        if loc is not None and loc.text:
            urls.append(loc.text)
    return urls


def check_url(url):
    """Check a single URL and return tuple (url, status)."""
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 404:
            return (url, '404 Not Found')
        else:
            return (url, 'OK')
    except requests.RequestException as e:
        return (url, f"Error: {e}")


def generate_html_report(results, output_file='sitemap_report.html'):
    """Generate a simple HTML report showing URL and status."""
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    html_content = f"""
    <html>
    <head>
        <title>Sitemap Check Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; }}
            th {{ background-color: #f2f2f2; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
            .ok {{ color: green; }}
            .notfound {{ color: red; }}
        </style>
    </head>
    <body>
        <h2>Sitemap Check Report</h2>
        <p>Generated on: {now}</p>
        <table>
            <tr><th>URL</th><th>Status</th></tr>
    """

    for url, status in results:
        status_class = "ok" if status == "OK" else "notfound"
        html_content += f"<tr><td><a href='{url}' target='_blank'>{url}</a></td><td class='{status_class}'>{status}</td></tr>\n"

    html_content += """
        </table>
    </body>
    </html>
    """

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"\nHTML report generated: {output_file}")


def main():
    urls = get_urls_from_sitemap(SITEMAP_URL)
    print(f"Found {len(urls)} URLs in sitemap.")

    results = []
    # Use ThreadPoolExecutor to check URLs in parallel
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_url = {executor.submit(check_url, url): url for url in urls}
        for future in as_completed(future_to_url):
            url_result = future.result()
            results.append(url_result)
            print(f"{url_result[1]}: {url_result[0]}")

    # Sort results alphabetically for nicer HTML report
    results.sort(key=lambda x: x[0])
    generate_html_report(results)


if __name__ == "__main__":
    main()