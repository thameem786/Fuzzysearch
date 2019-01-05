from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import json
from helper import WordMatching
from constants import MIN_CHARS

wm = WordMatching("word_search.tsv")
app = Flask(__name__)
CORS(app)


@app.route("/search", methods=['GET'])
def fuzzysearch():
    word = request.args.get("word")
    word = ''.join(filter(lambda x: x.isalpha(), word))
    if not word or len(word) < MIN_CHARS:
        body = json.dumps({
            "message": f"Please enter atleast {MIN_CHARS} characters to search",
            "data": []
        })
    else:
        result = wm.top_matches(word)
        body = json.dumps({
            "message": "match successful.",
            "data": [data[0] for data in result]
        })
        print (body)
    return jsonify(body)

if __name__ == '__main__':
    app.run(debug=False, threaded=True)