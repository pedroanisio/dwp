import json
import re
from collections import Counter
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

# Download necessary NLTK data
try:
    stopwords.words("english")
except LookupError:
    nltk.download("stopwords")

try:
    nltk.data.find("corpora/wordnet.zip")
except LookupError:
    nltk.download("wordnet")


def extract_text_from_json(data):
    """Recursively extract text from the JSON structure."""
    text_content = []

    if isinstance(data, dict):
        if data.get("type") == "text" and "content" in data:
            text_content.append(data["content"])
        for key, value in data.items():
            text_content.extend(extract_text_from_json(value))
    elif isinstance(data, list):
        for item in data:
            text_content.extend(extract_text_from_json(item))

    return text_content


def create_bag_of_words(input_json_path, output_json_path):
    """
    Creates a bag of words from a JSON file and saves it to another JSON file.
    """
    try:
        with open(input_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: The file {input_json_path} was not found.")
        return
    except json.JSONDecodeError:
        print(f"Error: The file {input_json_path} is not a valid JSON file.")
        return

    # Extract text
    all_text = " ".join(extract_text_from_json(data))

    # Tokenize: split into words, convert to lowercase, remove punctuation
    words = re.findall(r"\b\w+\b", all_text.lower())

    # Initialize lemmatizer and stop words
    lemmatizer = WordNetLemmatizer()
    stop_words = set(stopwords.words("english"))

    # Lemmatize and remove stop words
    lemmatized_words = [
        lemmatizer.lemmatize(word) for word in words if word not in stop_words
    ]

    # Count word frequencies
    bag_of_words = Counter(lemmatized_words)

    # Filter out words that appear only once
    filtered_bow = {word: count for word, count in bag_of_words.items() if count > 1}

    # Save the bag of words to a file
    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(filtered_bow, f, indent=2, ensure_ascii=False)

    print(f"Bag of words created and saved to {output_json_path}")

    return filtered_bow


def sort_bag_of_words(bag_of_words, output_json_path):
    """Sorts the bag of words by frequency in descending order."""
    sorted_bow_list = sorted(bag_of_words.items(), key=lambda item: item[1], reverse=True)

    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(dict(sorted_bow_list), f, indent=2, ensure_ascii=False)

    print(f"Sorted bag of words saved to {output_json_path}")
    return sorted_bow_list


def format_bag_of_words_to_88_cols(sorted_bow_list, output_txt_path):
    """Formats the bag of words into 88-column lines."""
    with open(output_txt_path, "w", encoding="utf-8") as f:
        current_line = ""
        for word, count in sorted_bow_list:
            pair = f"{word},{count}"
            if not current_line:
                current_line = pair
            elif len(current_line) + 1 + len(pair) <= 88:  # +1 for the comma separator
                current_line += f",{pair}"
            else:
                f.write(current_line + "\n")
                current_line = pair
        if current_line:
            f.write(current_line + "\n")
    print(f"Formatted bag of words saved to {output_txt_path}")


if __name__ == "__main__":
    lemmatized_bow = create_bag_of_words(
        "pci.json", "pci_bag_of_words_filtered.json"
    )
    if lemmatized_bow:
        sorted_bow_list = sort_bag_of_words(
            lemmatized_bow, "pci_bag_of_words_filtered_sorted.json"
        )
        format_bag_of_words_to_88_cols(
            sorted_bow_list, "pci_bag_of_words_filtered_formatted.txt"
        )
