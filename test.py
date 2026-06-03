import childespy
# Get all collections in the CHILDES database
collections = childespy.get_collections()

# Get all transcripts in the "childes" collection
transcripts = childespy.get_transcripts(collection = "Eng-na")
# Get all utterances where a specific child is the target
utterances = childespy.get_utterances(target_child="Adam")
print(utterances.head())