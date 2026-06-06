from pathlib import Path
import re
import math


def tokenize_file(filepath):
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            yield from TOKEN_RE.findall(line)


EXCLUDE_DIRS = {
    "node_modules",
    "venv",
    ".venv",
    "packages",
    "git",
    "cache",
    ".DS_STORE",
    "tests",
    "spec",
    "specs",
    "test",
    "__tests__",
    "__test__",
}
INCLUDE_DIRS = {"app_automate"}
TEXT_EXTENSIONS = {
    ".py",
    ".java",
    ".kt",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".go",
    ".cpp",
    ".c",
    ".h",
    ".hpp",
    ".md",
    ".txt",
    ".json",
    ".yaml",
    ".yml",
    ".xml",
    ".html",
    ".css",
    ".sh",
    ".rb",
}
TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")


def get_freq_q_in_doc(query, doc_id, all_tokens_data) -> int:
    for freq, c_doc_id in all_tokens_data[query]:
        if doc_id == c_doc_id:
            return freq
    return 0


if __name__ == "__main__":
    current_path = Path(__file__).resolve().parent
    parent_dir = current_path.parent
    temp_file_path = current_path / "temp.txt"
    all_tokens_data = {}
    doc_lengths = {}
    total_docs = 0
    cnt = 0

    for file_path in parent_dir.rglob("*"):
        if not file_path.is_file():
            continue

        if any(part in file_path.parts for part in EXCLUDE_DIRS):
            continue

        if not any(part in file_path.parts for part in INCLUDE_DIRS):
            continue

        if file_path.suffix.lower() not in TEXT_EXTENSIONS:
            continue

        print(f"Reading: {file_path}")
        # print(f"cid: {current_doc_id}")
        if cnt > 10:
            break
        current_doc_id = cnt
        cnt = cnt + 1
        doc_length = 0
        total_docs = total_docs + 1

        try:
            for token in tokenize_file(file_path):
                if all_tokens_data.get(token):
                    # print(f"token found already: {token}")
                    token_details = all_tokens_data[token]
                    # print(f"td already existing data: {token_details}")
                    flag = False
                    for i, val in enumerate(token_details):
                        freq, doc_id = val
                        if doc_id == current_doc_id:
                            # print(f"updating the freq: {token} - cf: {freq}")
                            token_details[i] = [freq + 1, doc_id]
                            flag = True
                    if not flag:
                        token_details.append([1, current_doc_id])
                else:
                    token_details = [[1, current_doc_id]]
                    # print(f"new td creating: {token_details}")

                # print(f"final td: {token_details}")
                doc_length = 1 + doc_length
                all_tokens_data[token] = token_details
        except Exception as e:
            print(f"Could not read {file_path}: {e}")

        doc_lengths[current_doc_id] = doc_length

    with open(temp_file_path, "w", encoding="utf-8") as out:
        for token, val in all_tokens_data.items():
            out.write(f"{token} -> ")
            out.write("\n")
            for freq, doc_id in val:
                doc_len = doc_lengths[doc_id]
                out.write(f"Doc {doc_id}: {freq} times")
                out.write("\n")
                # print(f"{doc_id}: {freq} times")

    avgdl = sum(doc_lengths.values()) / len(doc_lengths)
    query = input("Enter your query: ")
    if not query or query == "":
        print(f"Please enter a valid query: {query}")
        exit(1)
    parsed_query = TOKEN_RE.findall(query)[0]
    print(f"{parsed_query}")
    doc_scores = 0
    k_1 = 1.2
    b = 0.75
    query_token_details = all_tokens_data.get(parsed_query)
    if query_token_details is None:
        print("Query is not present in any doc. Returning....")
        exit(0)

    nq = len(query_token_details)
    idf = math.log(1 + ((total_docs - nq + 0.5) / (nq + 0.5)))
    total_score = []

    for freq, doc_id in query_token_details:
        length_of_this_doc = doc_lengths[doc_id]
        score = idf * (freq * (k_1 + 1)) / (freq + k_1 * (1 - b + b * (length_of_this_doc / avgdl)))
        total_score.append((score, doc_id))

    total_score.sort(reverse=True)
    for val in total_score:
        print(val)
