import os
import sys
import json
import time
import urllib.request

REPO_ID = "R_kgDOVkf2yA"
CATEGORY_ID = "DIC_kwDOVkf2yM4DKesQ"  # Q&A Category
GRAPHQL_URL = "https://api.github.com/graphql"

def run_graphql(token, query, variables=None):
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        GRAPHQL_URL,
        data=data,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "DiscussionsEngine/1.0"
        }
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def create_all_questions():
    token = os.environ["GH_TOKEN"]
    with open("qa_dataset.json", "r", encoding="utf-8") as f:
        qa_list = json.load(f)

    created = []
    print(f"Creating {len(qa_list)} discussions...")
    for idx, item in enumerate(qa_list, 1):
        query = """
        mutation CreateDisc($repoId: ID!, $catId: ID!, $title: String!, $body: String!) {
          createDiscussion(input: {
            repositoryId: $repoId,
            categoryId: $catId,
            title: $title,
            body: $body
          }) {
            discussion {
              id
              number
              title
            }
          }
        }
        """
        vars = {
            "repoId": REPO_ID,
            "catId": CATEGORY_ID,
            "title": item["title"],
            "body": item["question"]
        }
        resp = run_graphql(token, query, vars)
        disc = resp.get("data", {}).get("createDiscussion", {}).get("discussion")
        if disc:
            print(f"[{idx}/{len(qa_list)}] Created discussion #{disc['number']}: {disc['title']}")
            created.append({
                "number": disc["number"],
                "id": disc["id"],
                "title": disc["title"],
                "answer": item["answer"]
            })
        else:
            print(f"Error on {item['title']}: {resp}")
        time.sleep(0.5)

    with open("created_discussions.json", "w", encoding="utf-8") as f:
        json.dump(created, f, indent=2)
    print("All discussions successfully created.")

def mark_all_answers():
    token = os.environ["GH_TOKEN"]
    if not os.path.exists("comments_to_mark.json"):
        print("comments_to_mark.json not found.")
        return

    with open("comments_to_mark.json", "r", encoding="utf-8") as f:
        comments = json.load(f)

    print(f"Marking {len(comments)} answers as accepted...")
    for idx, item in enumerate(comments, 1):
        query = """
        mutation MarkAns($id: ID!) {
          markDiscussionCommentAsAnswer(input: {id: $id}) {
            discussion {
              id
              number
            }
          }
        }
        """
        resp = run_graphql(token, query, {"id": item["commentId"]})
        if "data" in resp and resp["data"].get("markDiscussionCommentAsAnswer"):
            print(f"[{idx}/{len(comments)}] Marked answer for #{item.get('number', idx)}")
        else:
            print(f"Error marking #{item.get('number', idx)}: {resp}")
        time.sleep(0.5)

if __name__ == "__main__":
    op = sys.argv[1] if len(sys.argv) > 1 else "create_questions"
    if op == "create_questions":
        create_all_questions()
    elif op == "mark_answers":
        mark_all_answers()
    else:
        print(f"Unknown operation: {op}")
