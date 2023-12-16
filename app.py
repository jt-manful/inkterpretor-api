import json
from flask import Flask, request, jsonify
from handwriting_extraction import detect_document
from text_summarizer import text_summarizer
from title_generator import title_generator
from flask_cors import CORS, cross_origin
import pyrebase
import datetime
#import functions_framework



# initialize flask app
app = Flask(__name__)
CORS(app)

firebaseConfig = {
    
     }

firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()
db = firebase.database()
storage = firebase.storage()

#Initialze person as dictionary
person = {"is_logged_in": False, "name": "", "email": "", "uid": ""}



# @functions_framework.http
# def entry_point(request):
#     if 'register' in request.path and request.method == "POST":
#         return register()
#     elif 'login' in request.path and request.method == "POST":
#         return login()
#     elif 'signout' in request.path and request.method == "POST":
#         return signout()
#     elif 'users' in request.path and request.method == "GET":
#         return get_user()
#     elif 'upload_image' in request.path and request.method == "POST":
#         return upload_image()
#     elif 'post_text_to_sum' in request.path and request.method == "POST":
#         return post_text()
#     elif 'view_document' in request.path and request.method == "POST":
#         return view_document()
#     elif 'view_history' in request.path and request.method == "POST":
#         return view_history()
#     elif 'delete_document' in request.path and request.method == "POST":
#         return delete_document()
#     elif 'delete_history' in request.path and request.method == "POST":
#         return delete_history()
#     else:
#         return jsonify({"error": "Invalid endpoint or method"}), 404



@app.route("/register", methods=['POST'])
@cross_origin()
def register():

    if request.method == "POST":  
        result = json.loads(request.data)          
        email = result["email"]
        uname = result["uname"]
        password = result["pass"]
        cpass = result["cpass"]

        if password != cpass:
            return 'passwords not the same', 400
       

        try:
            auth.create_user_with_email_and_password(email, password) 
            user = auth.sign_in_with_email_and_password(email, password) 

            global person
            person["is_logged_in"] = True
            person["email"] = user["email"]
            person["uid"] = user["localId"]
            person["name"] = uname
            
            #Append data to the firebase realtime database
            data = {"name": uname, "email": email, "last_logged_in": datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S")}
            db.child("users").child(person["uid"]).set(data)


            return 'registration successful', 200
        except:
            return "failed to register", 400
        
    if person["is_logged_in"] == True:
        return jsonify({'registration successful'}), 200
    else:
        return jsonify({'registration failed'}), 400
    

@app.route("/login", methods=['POST'])
def login():
    if request.method == "POST":        
        result = json.loads(request.data)   
        email = result["email"]
        password = result["pass"]

        try:
            #Try signing in the user with the given information
            user = auth.sign_in_with_email_and_password(email, password)
            #Insert the user data in the global person
            global person
            person["is_logged_in"] = True
            person["email"] = user["email"]
            person["uid"] = user["localId"]
            #Get the name of the user
            data = db.child("users").get()
            

            if data and person["uid"] in data.val():
                person["name"] = data.val()[person["uid"]]["name"]                # Update last login time
                db.child("users").child(person["uid"]).update({"last_logged_in": datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S")})
            else:
                person["name"] = "User"

            return jsonify({'success':'login successful'}), 200   
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 400   
 
        
    if person["is_logged_in"] == True:
        return jsonify({'success':'login successful'}), 200
    else:
        return jsonify({'error':'loign failed'}), 400  
    


@app.route("/signout", methods=['POST'])
def signout():
    try:
        person["is_logged_in"] = False
        person["email"] = ""
        person["uid"] = ""
        person["name"] = ""
        auth.current_user = None
        return "signout complete", 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400   

   


@app.route("/users", methods=['GET'])
def get_user():
     #Get the name of the user
        data = db.child("users").get()
        if data.val():
            # Iterate through users and print usernames
            for user_id, user_data in data.val().items():
                username = user_data.get('name', '')  # assuming 'name' is the key for username
                return (f"User ID: {user_id}, Username: {username}"), 200
        else:
            return "No users found.", 400
    

@app.route('/upload_image', methods=['POST'])
def upload_image():
    
    if person["is_logged_in"] == False or request.method != 'POST':
        return jsonify ("failed to complete task login first"), 400
    
     #Get image
    if 'image' not in request.files:
        return jsonify("No image file provided."), 400
    
    # save image to  bucket
    image = request.files['image']
    destination_path = "images/" + image.filename
    storage.child(destination_path).put(image)
    download_url = storage.child(destination_path).get_url(None)

    # Get document_id from JSON data
    if 'document_id' not in request.form:
        return jsonify("No 'document_id' provided in JSON data."), 400
    document_id = request.form['document_id']


    try:
        text = detect_document(download_url)
        title = title_generator(text)
        time = datetime.datetime.now().strftime("%m%d%Y-%H:%M:%S")
        today = datetime.datetime.now().strftime("%m-%d-%Y")
        data = {'title':title, 'content': text, 'type': 'handwritten', 'timestamp':time, 'img_url':download_url}

        if len(document_id) == 0:
            new_document_id = 'document-'+str(time)
            document_ids = db.child('user_document').child(person["uid"]).child(today).get().val()

            if document_ids is None:
                document_ids = {}
                document_ids[0] = new_document_id
                db.child('user_document').child(person['uid']).child(today).set(document_ids)
                documents_list = {}
                documents_list[0] = data
                db.child('document').child(new_document_id).set(documents_list)
                return jsonify({"success": True, "download_url": download_url, 'text':text }), 200
            
            elif document_ids is not None:
                documents_list = {}
                documents_list[0] = data
                # db.child('user_document').child(person['uid']).child(today).set(document_ids)
                document_ids = db.child('user_document').child(person["uid"]).child(today).get().val()
                document_ids.append(new_document_id)
                db.child('user_document').child(person["uid"]).child(today).set(document_ids)
               
                db.child('document').child(new_document_id).set(documents_list)
                return jsonify({"success": True, "download_url": download_url, 'text':text }), 200

        elif len(document_id) != 0:
            try:
                documents_list = db.child('document').child(document_id).get().val()
                documents_list.append(data)
                db.child('document').child(document_id).set(documents_list)
                return jsonify({"success": True, "download_url": download_url, 'text':text }), 200

            except Exception as e:
                return jsonify({"success": False, "error": str(e)}), 400   
        
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400       
     
    

@app.route('/post_text_to_sum', methods=['POST'])
def post_text():

    if person["is_logged_in"] == False or request.method != 'POST':
        return jsonify ("failed to complete task login first"), 400
    
    result = json.loads(request.data) 
    if  'text_to_sum' not in result:
         return jsonify({'error': 'No text foud'}), 400
    
    text_to_sum = result['text_to_sum']

    if 'document_id' not in result:
        return jsonify("No 'document_id' provided in JSON data."), 400

    document_id = result['document_id']

    try:
        summed_text = text_summarizer(text_to_sum)
        title = title_generator(summed_text)
        time = datetime.datetime.now().strftime("%m%d%Y-%H:%M:%S")
        today = datetime.datetime.now().strftime("%m-%d-%Y")
        data = {'title':title,'content': summed_text, 'type': 'text-sum', 'timestamp':time}
        

        if len(document_id) == 0:
            new_document_id = 'document-'+str(time)
            document_ids = db.child('user_document').child(person["uid"]).child(today).get().val()

            if document_ids is None:
                document_ids = {}
                document_ids[0] = new_document_id
                db.child('user_document').child(person['uid']).child(today).set(document_ids)
                documents_list = {}
                documents_list[0] = data
                db.child('document').child(new_document_id).set(documents_list)
                return jsonify({"success": True, 'text': summed_text }), 200
            
            elif document_ids is not None:
              
                documents_list = {}
                documents_list[0] = data
                # db.child('user_document').child(person['uid']).child(today).set(document_ids)
                document_ids = db.child('user_document').child(person["uid"]).child(today).get().val()
                document_ids.append(new_document_id)
                db.child('user_document').child(person["uid"]).child(today).set(document_ids)
               
                db.child('document').child(new_document_id).set(documents_list)
                return jsonify({"success": True, 'text': summed_text}), 200

        elif len(document_id) != 0:
            try:
                documents_list = db.child('document').child(document_id).get().val()
           
                documents_list.append(data)
                db.child('document').child(document_id).set(documents_list)
                return jsonify({"success": True, 'text': summed_text}), 200

            except Exception as e:
                return jsonify({"success": False, "error": str(e)}), 400   
        
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400       
     
      



@app.route('/view_document', methods=['POST'])
def view_document():
    if person["is_logged_in"] == False or request.method != 'POST':
        return jsonify ("failed to complete task login first"), 400

    if 'document_id' not in request.json:
        return jsonify("No 'document_id' provided in JSON data."), 400

    document_id = request.json['document_id']

    try: 
        document_data = db.child('document').child(document_id).get().val()

        if document_data is None:
            return jsonify(f"document with id {document_id} was not found"), 200

       
        return jsonify(document_data), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400  



@app.route('/view_history', methods=['POST'])
def view_history():
    if person["is_logged_in"] == False or request.method != 'POST':
        return jsonify ("failed to complete task login first"), 400

    try: 
        person_documents = db.child('user_document').child(person["uid"]).get().val()
        result_dict = {}
       
       
        if person_documents is not None:
            # Retrieve document information for each document ID
            for days, values in person_documents.items():
                results = []
                for document_id in values:
                    document_info = db.child('document').child(document_id).get().val()
                    data = {'document_id':document_id,
                            'title':document_info[0]['title']
                            }
                    results.append(data)
                    result_dict[days] = results
                
            return result_dict, 200
        else:
             return jsonify('no history'), 201

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400  



@app.route('/delete_document', methods=['POST'])
def delete_document():
    if person["is_logged_in"] == False or request.method != 'POST':
        return jsonify ("failed to complete task login first"), 400
    if 'document_id' not in request.json:
        return jsonify("No 'document_id' provided in JSON data."), 400

    document_id = request.json['document_id']

    try:
        # # Delete user document from the database
        # db.child('user_document').child(person["uid"]).remove()
        # if db.child('document').child(document_id).get().val() is None:
        #      return jsonify(f"document with id {document_id} was not found"), 200

        # print("user docs ", db.child("user_document").child(person["uid"]).get().val())
        for date, document_ids in db.child("user_document").child(person["uid"]).get().val().items():
            # print("dates", date)
            # Iterate over the document IDs
            for docum in document_ids:
                # print("entered doc", document_id, "pc doc", docum)
                if docum == document_id:  
                    # print("true that")  
                # # Now you can use the document_id as needed (e.g., delete it)
                    # print("doc ids ", db.child("user_document").child(person["uid"]).child(date).get().val())
                    docs =  db.child("user_document").child(person["uid"]).child(date).get().val()
                    # print("docs going", docs)
                    new_doc = []
                    for item in docs:
                        if item !=  document_id:
                            new_doc.append(item)
                    # print("new", new_doc)
                    db.child("user_document").child(person["uid"]).child(date).set(new_doc)

        return jsonify(f"document with id {document_id} deleted successfully"), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route('/delete_history', methods=['POST'])
def delete():
    if person["is_logged_in"] == False or request.method != 'POST':
        return jsonify ("failed to complete task login first"), 400

    try:
        # Delete user history from the database
        db.child('user_document').child(person["uid"]).remove()


        return jsonify("User history deleted successfully"), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


if __name__ == '__main__':
    app.run((host="0.0.0.0", port=5000, debug=True)
