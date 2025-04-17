TEXT_PREPROCESSING_PROMPT = """
Task Description
Please convert the following transcript into subtitle format suitable for AI voice synthesis. These subtitles will be used for AI voice generation, so special attention is needed to natural pause points, avoiding AI pausing at inappropriate positions.
Processing Principles
1. Balanced Segmentation Principle
* Each segment should be around 10-20 words in length (not exceeding 25 words)
* Each segment should express a relatively complete semantic unit
* Short complete sentences (under 7 words) can form their own segment
* Longer sentences (over 25 words) need appropriate segmentation
2. Segmentation Position Priority
1. At periods, question marks, exclamation marks, and other end-of-sentence punctuation
2. At semicolons, colons
3. At commas (choose semantically complete positions)
4. Before transition words (such as: but, however, nevertheless, yet, etc.)
5. Before causal relationship words (such as: therefore, thus, hence, etc.)
6. Between parallel structures
3. Prohibited Segmentation Positions
* Between subject and predicate (e.g., "The company directors / decided")
* Between verb and object (e.g., "improve / efficiency")
* Between adjective and noun (e.g., "important / document")
* Between article and noun (e.g., "a / apple")
* Between prepositions and their objects (e.g., "in / the house")
* Between conjunctions and subsequent content (e.g., "if / it rains")
4. Punctuation Handling
* Retain original punctuation
* When segmenting, keep end punctuation in that segment
* If appropriate punctuation is lacking in the original text, commas may be added at semantically complete points
Special Situation Handling
* Dialogue content: Each speaker's content can be treated as an independent unit
* Listed items: Every 1-2 listed items can form a segment
* Number sequences: Avoid separating numbers from their units
* Proper nouns: Maintain integrity, do not split
Output Format
Output the processed text in the following format:
1. Each segment on a separate line
2. Leave a blank line between segments and add "---"
3. No need to add timestamps or numbering

Transcript Content
Please process the following transcript:
{text}
"""