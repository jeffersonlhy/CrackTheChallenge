import logging
import json

from flask import request, jsonify

from codeitsuisse import app

logger = logging.getLogger(__name__)

@app.route('/asteroid', methods=['POST'])
def asteroid():

    def calScore(count):
        if count >= 10:
            return count * 2
        elif count >=7:
            return count * 1.5
        else:
            return count


    def findScore(str, c):
        # assume str = "#CCCAAA#"
        l = c - 1
        r_limit = len(str)
        r = c + 1
        if l <= 0 or r >= r_limit - 1:
            return 1
        score = 1
        as_count = 0
        while str[l] == str[r] and l >= 0 and r < r_limit and str[l] != "#" and str[r] != "#":
            moved_l = False
            moved_r = False
            tried_while_l = False
            tried_while_r = False
            as_type = str[l]
            as_count += 2
            # l -= 1
            # r += 1
            # nevigate l to left
            while l >= 0 and str[l] == as_type and str[l] == str[l-1]:
                tried_while_l = True
                as_count += 1
                l -= 1
                    
            # nevigate r to right
            while r <= r_limit - 2 and str[r] == str[r+1]:
                as_count += 1
                r += 1

                
            # Calculate
            score += calScore(as_count)
            as_count = 0

            l -= 1
            r += 1

        return score



    
    data = request.get_json()
    output = []

    logging.info(f"received {data}")
    numList = data['test_cases']
    for case in numList:
        output_case = {
            'input': case,
            'score': 1,
            'origin': 1
        }
        mod_case = "#" + case + "#"
        for c in range(1, len(mod_case)-1):
            score = findScore(mod_case, c)
            if score >= output_case['score']:
                output_case['score'] = score
                output_case['origin'] = c - 1
        output.append(output_case)

    
    return json.dumps(output)

