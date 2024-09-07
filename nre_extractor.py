import os
import base64
import time
import json
import threading
import vertexai
from vertexai.generative_models import GenerativeModel, Part, SafetySetting, FinishReason,GenerationConfig


def generate(directory,fileName):
    vertexai.init(project="arctic-pad-432823-c0", location="us-central1")
    model = GenerativeModel(
        "gemini-1.5-pro-001",
    )
    
    rawDirectory = "Data/" + directory + "/raw"
    file_path = os.path.join(rawDirectory, fileName)

    data = open(file_path, "r").read()
    data_byte = data.encode("utf-8")
    MetaFile_encode = base64.b64encode(data_byte)

    MetaFile_decode = base64.b64decode(MetaFile_encode)
    data_decode = MetaFile_decode.decode("utf-8")
    

    text1 = """

The text file contain a transcript from a youtube political talk show podcast. Please analyze the provided text and extract the named entities. Then, generate a JSON file containing this data with the following format for each entity:

 

 {
  name: "<اسم الكيان المُستخرج>",
  original_text: "<الاسم باللغة الانجليزية اذا كان الكيان المستخرج انجليزي>",
  type: "<نوع الكيان المُستخرج>",
  description: "<   وصف مختصر باللغة العربية للكيان المستخرج، على الأقل أربع فقرات>"
 } 
 

**Entity Types to consider:**

* **PERSON:** شخصيات عامة 
* **LOCATION:** أماكن جغرافية (مدن، دول، مناطق)
* **ORGANIZATION:** مؤسسات ومنظمات
* **EVENT:** أحداث تاريخية أو هامة 
* **LAW:** قوانين ومُواثيق 
* **WORK_OF_ART:** أعمال فنية (كتاب، مُؤلف، etc.)
* **RELIGIOUS_FIGURE:** شخصيات دينية
* **PRODUCT:** منتجات تجارية
* **WORK_OF_ART:** أعمال فنية (كتاب، مُؤلف، etc.)
* **MEDIA:** مواد مُعلقة على الإنترنت (فيديو، صورة، etc.)
* **MISC:** أي نوع آخر من الكيانات التي لا تندرج تحت أي من الفئات السابقة

**Example:**

{
    name: "ميرل ستريب",
    original_text: "Meryl Streep",
    type: "PERSON",
    description: "ممثلة أمريكية شهيرة، حائزة على عدة جوائز أوسكار، تُعتبر من أعظم الممثلات في تاريخ السينما."
  }


remove all the slashes and backslashes to make sure the output reponse is correctly formatted json content
and put the entities inside Entities array

"""



    document1 = Part.from_data(
        mime_type="text/plain",
        data=MetaFile_decode
    )
        

    generation_config = {
        "max_output_tokens": 8192,
        "temperature": 0,
        "top_p": 0.95,
    }

    safety_settings = [
        SafetySetting(
            category=SafetySetting.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
            threshold=SafetySetting.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
        ),
        SafetySetting(
            category=SafetySetting.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
            threshold=SafetySetting.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
        ),
        SafetySetting(
            category=SafetySetting.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
            threshold=SafetySetting.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
        ),
        SafetySetting(
            category=SafetySetting.HarmCategory.HARM_CATEGORY_HARASSMENT,
            threshold=SafetySetting.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
        ),
    ]
    
     
    
    counter = 0
    stop_counter = threading.Event()

    def increment_counter():
        nonlocal counter
        while not stop_counter.is_set():
            print(f"\rProcessing... {counter}", end="", flush=True)
            counter += 1
            time.sleep(1)

    counter_thread = threading.Thread(target=increment_counter)
    counter_thread.start()

    try:
        EntDirectory = "Data/" + directory + "/entities"
        os.makedirs(EntDirectory, exist_ok=True)
        responses = model.generate_content(
            [text1, document1],
            generation_config=generation_config,
            safety_settings=safety_settings,
        )
        
        mainResponse = responses.candidates[0].content.parts[0].text

        
        if is_json(mainResponse):
           fileName2 = fileName.replace(".txt","")
           generated_file = "Extracted_entities_" + fileName2 + ".json"
           output_file = os.path.join(EntDirectory, generated_file)
           print("----------------------------------")
           print("Correct JSON", output_file)
           print("----------------------------------")
           mainResponse = json.loads(mainResponse)
           with open(output_file, "w", encoding="utf-8") as f:
                json.dump(mainResponse, f, ensure_ascii=False, indent=4)
        else:
           fileName2 = fileName.replace(".txt","")
           generated_file = "Null_entities_" + fileName2 + ".json"
           output_file = os.path.join(EntDirectory, generated_file)
           print("----------------------------------")
           print("Not Correct JSON", output_file)
           print("----------------------------------")
           mainResponse = mainResponse.replace("```json", "")
           mainResponse = mainResponse.replace("`", "")
           mainResponse = mainResponse.replace("\n", "")
           mainResponse = mainResponse.replace("\\", "").replace('/', "")
           mainResponse = mainResponse.replace(r"/", "")
           # Remove first and last character from mainResponse
           mainResponse = mainResponse[1:-1]
           with open(output_file, "w", encoding="utf-8") as f:
                json.dump(mainResponse, f, ensure_ascii=False, indent=4)
        
        
        print(f"Entities saved to: {generated_file}")
    finally:
        stop_counter.set()
        counter_thread.join()
        print(f"\nScript finished. Total processing time: {counter} seconds")
def is_json(myjson):
  try:
    json.loads(myjson)
  except ValueError as e:
    return False
  return True

# generate("aljazeera360","aljazeera360_0_0WAtP28eD1c.txt")  
directory2 = 'AlbesatAhmadi'
newDirectory = "Data/" + directory2 + "/raw"
counter = 1
try:
    for filename in os.listdir(newDirectory):
        if ".processed." in filename:
            print("Processed :: ", filename)
            print("----------------------------------")
            continue
        else:
            generate(directory2,filename)
            oldname = os.path.join(newDirectory, filename)
            newname = filename.replace(".",".processed.")
            newname = os.path.join(newDirectory, newname)
            os.rename(oldname, newname) 
            print("Done :: ", counter, " " , filename)
            print("----------------------------------")
            counter += 1
        # if counter > 10:
        #     break
except FileNotFoundError:
    print(f"Directory not found: {newDirectory}")
except PermissionError:
    print(f"Permission denied to access directory: {newDirectory}")

print("Script execution stopped.")
exit()