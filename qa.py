from langchain.document_loaders import DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import SentenceTransformerEmbeddings
from langchain.vectorstores import Chroma
from langchain.chat_models import AzureChatOpenAI
from langchain.chains.question_answering import load_qa_chain
from langchain.chains import RetrievalQAWithSourcesChain, RetrievalQA
from langchain.prompts import PromptTemplate
import openai
import os

class Query():
    def __init__(self, directory='documents'):
        self.directory = directory
        self.documents = self.load_docs(self.directory)
        self.docs = self.split_docs(self.documents)
        self.hierarchy = """
                            C:/Users/felip/Documents/Concurso
                            |---archivos.csv
                            |---chroma_db
                            |   |---chroma.sqlite3
                            |   |---d9ea1cbb-1735-4a5e-8f3d-ced517601519
                            |   |   |---data_level0.bin
                            |   |   |---header.bin
                            |   |   |---index_metadata.pickle
                            |   |   |---length.bin
                            |   |   |---link_lists.bin
                            |---converter.py
                            |---deleter.py
                            |   |---chroma.sqlite3
                            |---documents
                            |   |---0.txt
                            |   |---1.txt
                            |   |---10.txt
                            |   |---100.txt
                            |   |---101.txt
                            |   |---102.txt
                            |   |---103.txt
                            |   |---104.txt
                            |   |---105.txt
                            |   |---106.txt
                            |   |---107.txt
                            |   |---108.txt
                            |   |---109.txt
                            |   |---11.txt
                            |   |---110.txt
                            |   |---[Otros archivos omitidos]
                            |---embeddings.json
                            |---files
                            |---folders.py
                            |---qa.ipynb
                            |---query.py
                            |---quickstart.py
                            |---testing
                            |   |---deleter.py
                            |   |---distributions.ipynb
                            |   |---distributions_data.py
                            |   |---doi.txt
                            |   |---log.txt
                            |   |---metrics.py
                            |   |---pdf2html.py
                            |   |---pfizer.py
                            |   |---pfizer.txt
                            |   |---request.py
                            |   |---results.txt
                            |   |---results_without_zeros.txt
                            |---wpp.txt"""
        self.deployment_name = "codecompass-gpt-16"
        self.emb_name = "codecompass_emb"

        os.environ["OPENAI_API_KEY"] = "f9e438c0871042d1bfdfb01cfd30d79e"
        os.environ["OPENAI_API_BASE"] = "https://codecompassopenai.openai.azure.com/"
        os.environ["OPENAI_API_VERSION"] = '2023-05-15'

    def make_db(self):
        model_name = "gpt-3.5-turbo-16k"
        self.embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
        self.db = Chroma.from_documents(self.docs, self.embeddings)
        self.llm = AzureChatOpenAI(model_name=model_name, deployment_name=self.deployment_name)

    def load_docs(self, directory):
        loader = DirectoryLoader(directory)
        documents = loader.load()
        return documents

    def split_docs(self, documents,chunk_size=3000,chunk_overlap=20):
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        docs = text_splitter.split_documents(documents)
        return docs
    
    def make_query(self, question = "What should a dog eat?"):
        
        matching_docs = self.db.similarity_search(question)
        template_string = """You are an assistant that helps developers document \
                or answer questions about software development projects. The project's \
                current folder hierarchy is denoted by #### characters and is the following: \
                ####{hierarchy}####. Use the following context to answer the query made by \
                user. The context is usually some useful files or fragments of files of the \
                project that you could use and is sorrounded by triple backticks. \
                If you don't know the answer, don't try to answer it. Just say you don't know.
                You have to answer the query in a way that is useful for the user, and use \
                the language of the user.
                context: ´´´{summaries}´´´
                question: ´´´{question}´´´
                answer:"""

        qa = RetrievalQAWithSourcesChain.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.db.as_retriever(),
            chain_type_kwargs={
                "prompt": PromptTemplate(
                    template=template_string,
                    input_variables=["hierarchy", "summaries", "question"]
                )
            }
        )
        return qa({ "question": question, "hierarchy": self.hierarchy, "summaries": matching_docs})
    
p = Query()
p.make_db()

while True:
    query = str(input("Query: "))
    print(p.make_query(query))
        