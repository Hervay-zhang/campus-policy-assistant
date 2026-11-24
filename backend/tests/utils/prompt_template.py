from langchain_core.prompts import ChatPromptTemplate


def getPromptTemplate(system:str,human:str):
	template = ChatPromptTemplate.from_messages([
		("system", system),
		("human", human)
	])
	return template