from flask import Flask, render_template, request, jsonify
import pandas as pd
import os
from nltk.corpus import stopwords, wordnet
import re
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from itertools import combinations


app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# ---------------------
def custom_preprocess_text(text):
    stop = stopwords.words("english")
    # Remove stopwords
    text = " ".join(x for x in text.split() if x not in stop)
    text = re.sub(r"&|-|_|/", " ", text)
    # also remove white spaces
    text = text.strip()
    # print(text,'Text Processing')
    return text


def get_synonyms(word):
    synonyms = set()
    for syn in wordnet.synsets(word):
        for lemma in syn.lemmas():
            synonyms.add(lemma.name().lower())
    return synonyms


def preprocess_text(text):
    # Tokenize, remove stopwords, and lemmatize
    stop_words = set(stopwords.words("english"))
    tokens = word_tokenize(text)
    tokens = [
        word.lower()
        for word in tokens
        if word.isalnum() and word.lower() not in stop_words
    ]
    lemmatizer = WordNetLemmatizer()
    tokens = [lemmatizer.lemmatize(word) for word in tokens]
    return tokens


def calculate_similarity(course1, course2):
    # Get synonyms for each course name
    synonyms1 = set()
    synonyms2 = set()

    for word in preprocess_text(course1):
        synonyms1.update(get_synonyms(word))

    for word in preprocess_text(course2):
        synonyms2.update(get_synonyms(word))
    # print(synonyms1, synonyms2)
    # Calculate Jaccard similarity
    intersection = len(synonyms1.intersection(synonyms2))
    union = len(synonyms1.union(synonyms2))
    similarity = intersection / union if union > 0 else 0

    return similarity


def check_similar(val1, val2):
    return calculate_similarity(val1, val2) >= 0.85


def find_missing_courses(curriculum_df, category_dict):
    missing_courses = {}

    for _, row in curriculum_df.iterrows():
        course_name = row["Course Name"]
        category = row["Category"]

        if category not in category_dict:
            missing_courses.setdefault(category, []).append(
                {"courseName": course_name, "creditHour": row["creditHour"]}
            )
        else:
            # Extract course names from the dictionaries in the category list
            cat_course_names = [
                cat_value["courseName"] for cat_value in category_dict[category]
            ]

            # Check for similarity using check_similar function
            if not any(
                check_similar(course_name, cat_course_name)
                for cat_course_name in cat_course_names
            ):
                missing_courses.setdefault(category, []).append(
                    {"courseName": course_name, "creditHour": row["creditHour"]}
                )

    return missing_courses


def checkPossibleWays(missing_courses, creditHour):
    possibleWays = {}
    for key, val in missing_courses.items():
        possibleWays[key] = []
        for i in range(1, len(missing_courses[key]) + 1):
            for j in combinations(missing_courses[key], i):
                if sum(course["creditHour"] for course in j) == creditHour:
                    possibleWays[key].append(j)
    return possibleWays


# ---------------------


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    # global creditCount, reasons, mis, allPossibleWays

    trnsfile = request.files["trnsfile"]
    hecfile = request.files["hecfile"]
    criteriafile = request.files["criteriafile"]
    # edit with current time
    filenames = [trnsfile.filename, hecfile.filename, criteriafile.filename]
    # Save the files to the upload folder
    trnsfile.save(os.path.join(app.config["UPLOAD_FOLDER"], trnsfile.filename))
    hecfile.save(os.path.join(app.config["UPLOAD_FOLDER"], hecfile.filename))
    criteriafile.save(os.path.join(app.config["UPLOAD_FOLDER"], criteriafile.filename))

    creditCount, reasons, mis, allPossibleWays = runHecValidator(filenames)

    return jsonify(
        {
            "creditCount": creditCount,
            "reasons": reasons,
            "mis": mis,
            "allPossibleWays": allPossibleWays,
        }
    )


def runHecValidator(filenames):
    creditCount = 0
    reasons = []
    mis = []
    allPossibleWays = []
    print("runHecValidator")
    print(filenames)

    transcript = pd.read_csv("uploads/" + filenames[0])
    df = pd.read_csv("uploads/" + filenames[1])
    criteria_df = pd.read_csv("uploads/" + filenames[2])
    df["Course Name"] = df["Course Name"].str.lower().apply(custom_preprocess_text)
    transcript["courseName"] = (
        transcript["courseName"].str.lower().apply(custom_preprocess_text)
    )
    categories = df["Category"].unique()
    criteria = criteria_df.set_index("Category")["Credit Hours"].to_dict()

    # filtered courses from transcript - passed - failed
    category_dict = {category: [] for category in categories}
    failed_courses = {category: [] for category in categories}

    for index2, row2 in transcript.iterrows():
        course_found = (
            False  # Flag to track if a course has been found for any category
        )
        for category in categories:
            for index, row in df[df["Category"] == category].iterrows():
                contDomain = "domain" in row2["courseName"].lower()
                if (
                    calculate_similarity(row["Course Name"], row2["courseName"]) >= 0.85
                    or contDomain
                ):
                    if (
                        row2["grade"] != "S"
                        and row2["grade"] != "F"
                        and row2["grade"] != "W"
                    ):
                        if contDomain:
                            if (
                                "supporting" in category.lower()
                                and "supporting" in row2["courseName"].lower()
                            ):
                                # print(row['Course Name'], ' -- ', row2['courseName'], '--' , category)
                                category_dict[category].append(
                                    {
                                        "courseName": row2["courseName"],
                                        "creditHour": row2["creditHour"],
                                    }
                                )
                                creditCount += row2["creditHour"]
                            elif (
                                "core" in category.lower()
                                and "core" in row2["courseName"].lower()
                                and "compulsory" in category.lower()
                            ):
                                # print(row['Course Name'], ' -- ', row2['courseName'], '--' , category)
                                category_dict[category].append(
                                    {
                                        "courseName": row2["courseName"],
                                        "creditHour": row2["creditHour"],
                                    }
                                )

                                creditCount += row2["creditHour"]
                            break
                        else:
                            # if category == 'University_Elective_Courses':
                            #     print(row['Course Name'], ' -- ', row2['courseName'], '--' , category)
                            # print(row['Course Name'], ' -- ', row2['courseName'], 'course Appending')
                            category_dict[category].append(
                                {
                                    "courseName": row2["courseName"],
                                    "creditHour": row2["creditHour"],
                                }
                            )
                            # trcourses[row2['type']].drop(index2, inplace=True)
                            creditCount += row2["creditHour"]
                            # if row2['creditHour'] == 3:
                            #     creditCount += 3
                            # else:
                            #     creditCount += 1

                            course_found = (
                                True  # Set the flag to True when a course is found
                            )
                        break  # Break the inner loop since the course is found
                    else:
                        print("Failed")
                        failed_courses[category].append(
                            {
                                "courseName": row2["courseName"],
                                "creditHour": row2["creditHour"],
                            }
                        )
        # Additional actions if needed based on whether the course is found or not
        if not course_found:
            # Perform additional actions if the course is not found for any category
            pass
    for key in category_dict:
        if criteria[key] <= sum(c["creditHour"] for c in category_dict[key]):
            reasons.append(f"Category {key} is complete")
        else:
            missing_creditHours = criteria[key] - sum(
                c["creditHour"] for c in category_dict[key]
            )
            missing_courses_dict = find_missing_courses(
                df[df["Category"] == key], {key: category_dict[key]}
            )
            # tell the user how many credit hours are missing
            # reasons.append(f"Category {key} is incomplete")
            reasons.append(
                f"Category {key} is incomplete.\n Credit hours missing: {missing_creditHours}"
            )
            if missing_creditHours > 0 or len(missing_courses_dict) > 0:
                # print(len(missing_courses_dict), 'length\n')
                allPossibleWays.append(
                    checkPossibleWays(missing_courses_dict, missing_creditHours)
                )
            mis.append(missing_courses_dict)
    return creditCount, reasons, mis, allPossibleWays


# Rest of your code continues here...
