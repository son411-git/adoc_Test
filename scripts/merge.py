import os
import re

def extract_tagged_region(lines, tag_name):
    """Extract lines inside a specific tag region."""
    start_tag = f"// tag::{tag_name}[]"
    end_tag = f"// end::{tag_name}[]"
    extracted, inside = [], False

    for line in lines:
        if start_tag in line:
            inside = True
            continue
        if end_tag in line:
            inside = False
            continue
        if inside:
            extracted.append(line)
    return extracted

def merge_lines(lines, base_dir):
    """Process raw lines, resolve includes recursively."""
    include_pattern = re.compile(r'\binclude::([^\[]+)\[([^\]]*)\]')

    merged_lines = []
    for line in lines:
        stripped = line.strip()

        # 주석인 줄은 그대로 유지
        if stripped.startswith('//'):
            merged_lines.append(line)
            continue

        match = include_pattern.search(line)
        if match:
            include_path = match.group(1).strip()
            options = match.group(2).strip()
            resolved_path = os.path.normpath(os.path.join(base_dir, include_path))

            if not os.path.exists(resolved_path):
                print(f'❌ 파일 없음: {resolved_path}')
                merged_lines.append(line)
                continue

            print(f'📥 포함 중: {resolved_path}')
            with open(resolved_path, 'r', encoding='utf-8') as f:
                included_lines = f.readlines()

            # tag 지정된 영역 추출
            tag_match = re.search(r'tag=([\w\-]+)', options)
            if tag_match:
                tag_name = tag_match.group(1)
                included_lines = extract_tagged_region(included_lines, tag_name)

            # 🔁 다시 병합 (경로 기준 바뀜)
            nested = merge_lines(included_lines, os.path.dirname(resolved_path))
            merged_lines.extend(nested)
        else:
            merged_lines.append(line)

    return merged_lines

def merge_adoc(entry_file, output_file):
    with open(entry_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    base_dir = os.path.dirname(entry_file)
    final_merged = merge_lines(lines, base_dir)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(final_merged)

    print(f'✅ 병합 완료: {output_file}')

# 🎯 실행 예시
if __name__ == "__main__":
    merge_adoc("index.adoc", "merged.adoc")