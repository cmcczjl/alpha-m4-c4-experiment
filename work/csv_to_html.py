#!/usr/bin/env python3
import csv
import os

INPUT_CSV = "data/output/form_result.csv"
OUTPUT_HTML = "data/output/report.html"

def csv_to_html(csv_path, html_path):
    if not os.path.isfile(csv_path):
        raise FileNotFoundError(f"Input CSV not found: {csv_path}")

    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        rows = list(reader)

    if not rows:
        raise ValueError("CSV file is empty")

    headers = rows[0]
    data_rows = rows[1:]

    html_content = ['<!DOCTYPE html>',
                    '<html lang="en">',
                    '<head>',
                    '  <meta charset="UTF-8">',
                    '  <title>Form Result Report</title>',
                    '  <style>',
                    '    table {border-collapse: collapse; width: 100%;}',
                    '    th, td {border: 1px solid #ddd; padding: 8px;}',
                    '    th {background-color: #f2f2f2;}',
                    '  </style>',
                    '</head>',
                    '<body>',
                    '  <h1>Form Result Report</h1>',
                    '  <table>',
                    '    <thead>',
                    '      <tr>'] 
    html_content += [f'        <th>{h}</th>' for h in headers]
    html_content += ['      </tr>',
                     '    </thead>',
                     '    <tbody>']
    for row in data_rows:
        html_content += ['      <tr>']
        html_content += [f'        <td>{cell}</td>' for cell in row]
        html_content += ['      </tr>']
    html_content += ['    </tbody>',
                     '  </table>',
                     '</body>',
                     '</html>']

    with open(html_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(html_content))

if __name__ == "__main__":
    csv_to_html(INPUT_CSV, OUTPUT_HTML)
    print(f"Report generated: {OUTPUT_HTML}")