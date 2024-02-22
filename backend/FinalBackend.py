from langchain_community.document_loaders import UnstructuredWordDocumentLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import OpenAIEmbeddings
from pinecone import Pinecone
import numpy as np    
import os
import getpass
import textract
import openai
import re


# filepath = os.path.join("uploads/f2.docx")
pc = Pinecone(api_key='d489c9e2-5765-423f-ab5a-5da2eabb2d14')  # create a Pinecone instance
pinecone_index = pc.Index("test1000")



def UploadFile(filepath,api_key):

    # ogText = textract.process(filepath)

    if filepath.endswith('.docx'):
        loader = UnstructuredWordDocumentLoader(filepath)

    elif filepath.endswith('.pdf'):
        loader = PyPDFLoader(filepath)
    else:
        raise ValueError("Unsupported file format. Supported formats: .docx, .pdf")
    
    file_content = loader.load()
    page_content = file_content[0].page_content

    # THIS HAS TO TURN TO FARHANS CODE 
    page_content = page_content.replace('\n', ' ')
    page_content = re.sub(r'[^a-zA-Z0-9\s]', '', page_content).lower()


    file_content[0].page_content = page_content

    text_splitter = CharacterTextSplitter(chunk_size=50, chunk_overlap=20)

    docs = text_splitter.split_documents(file_content)
    print("")
    print("DOCS",docs)
    print("")

    embeddings = OpenAIEmbeddings(openai_api_key=api_key)
 
    doc_contents = [doc.page_content for doc in docs]
    
    for doc in docs:
        print("DOC IS PRINTED ",doc)
        print("")

    print("")
    print("DOC CONTENTS ",doc_contents)
    print("")

    embedded_docs = embeddings.embed_documents(doc_contents)
    for i, doc in enumerate(docs):
        print("LOOK HERE ",docs[i].page_content)
        pinecone_index.upsert(vectors=[{"id": str(i), "values": embedded_docs[i], "metadata": {"text_chunk": docs[i].page_content}}])

    #this returns the title you dont actually need to send this back to frontend
    return docs[0].page_content




# print("Uploaded?",UploadFile(filepath,api_key))
# print("space")
# print("space")










query = "Which character is luigi?"

def GetResponse(query, api_key):
    embeddings = OpenAIEmbeddings(openai_api_key=api_key)
    return_vectors = pinecone_index.query(
        vector=embeddings.embed_query(query),
        top_k=10,
        include_values=True
    )  # returns top_k matches
    metadata_list = []

    for i, match in enumerate(return_vectors['matches']):
        vector_id_to_fetch = match['id']
        metadata_result = pinecone_index.fetch([vector_id_to_fetch])
        metadata = metadata_result['vectors'][vector_id_to_fetch]['metadata']
        metadata_list.append(metadata)
    print("")
    print("METADATA LIST ",metadata_list)
    print("")

    gpt_send = metadata_list[0]['text_chunk']
    print("GPT !!!!!!!!!!!!!!!!!",gpt_send)

    openai.api_key = api_key


    completion = openai.chat.completions.create(model="gpt-4-0125-preview",
        messages=[
        {"role": "user", "content": "Based on this background information ONLY: " + gpt_send + "ONLY use that background information word for word to answer this question: " + query}
    ])


    send_back = completion.choices[0].message.content
    print("")
    print("")

    # send_back is the final answer!
    return gpt_send,send_back

# print("RESPONSE: ",GetResponse(query, api_key))


