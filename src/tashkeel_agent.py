"""
API keys for LLM providers need to be stored in environment variables (or in .env file).

Multiple LLM providers are recommended for better accuracy.

TODO:
- Chunks should have overlap to increase the context size.
- Simulate line endings with a full stop, so the agent knows sentence structures.
"""
from argparse import ArgumentParser, Namespace
from collections import defaultdict
import logging
import asyncio
from typing import List, Tuple
from difflib import SequenceMatcher

from dotenv import load_dotenv
from agents import Runner

from my_agents.tashkeel_agent import create_openai_tashkeel_agent
from utils import make_chunks, extract_arabic_words, normalize_arabic_text, get_ratio_of_undiacritized_words

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Load environment variables
load_dotenv(override=True)


def reconstruct_chunk(original_text: str, diacritized_text: str) -> Tuple[str, bool]:
    """Reconstruct the original text from the diacritized text.
    Apply insertions, deletions and substitutions from the original text to the diacritized text.
    Differences are computed at word level and only for base letters.
    The number of words in the result must be the same as the number of words in original_text.
    """
    original_words = original_text.split()
    original_words_normalized = [normalize_arabic_text(w) for w in original_words]

    diacritized_words = [w for w in diacritized_text.split() if w]
    diacritized_words_normalized = [normalize_arabic_text(w) for w in diacritized_words]

    matcher = SequenceMatcher(None, original_words_normalized, diacritized_words_normalized)
    opcodes = matcher.get_opcodes()
    if len(opcodes) == 1 and opcodes[0][0] == 'equal':
        return ' '.join(diacritized_words), False

    reconstructed = []
    needs_rediacritization = False
    for type, start_i, end_i, start_j, end_j in opcodes:
        if type == 'equal':
            # Use the diacritized version
            reconstructed.extend(diacritized_words[start_j:end_j])
        elif type == 'delete':
            # If something is deleted in the diacritized version, insert it from the original
            for i in range(start_i, end_i):
                reconstructed.extend(original_words[start_i: end_i])
                if any(not w.isdigit() for w in original_words[start_i: end_i]):
                    needs_rediacritization = True
        elif type == 'insert':
            # If something new is introduced in the diacritized version, ignore it.
            pass
        elif type =='replace':
            if end_i - start_i == end_j - start_j:
                for i, j in zip(range(start_i, end_i), range(start_j, end_j)):
                    if original_words_normalized[i].isdigit():
                        reconstructed.append(original_words[i])
                    else:
                        reconstructed.append(original_words[i])
                        needs_rediacritization = True
            else:
                reconstructed.extend(original_words[start_i: end_i])
                needs_rediacritization = True
        else:
            raise ValueError(f"Invalid opcode: {type}")

    assert len(reconstructed) == len(original_words), f"""Reconstructed chunk length does not match the original chunk length.
    Original chunk length: {len(original_words)}, Reconstructed chunk length: {len(reconstructed)}
    Original chunk: {original_text}
    Diacritized chunk: {diacritized_text}
    Reconstructed chunk: {' '.join(reconstructed)}
    """
    return ' '.join(reconstructed), needs_rediacritization


async def run_tashkeel_with_agent(chunk: str, agent) -> str:
    """Get the vowelized version of the chunk using the provided agent.
    Repeat if the chunk needs to be rewritten due to discrepancy in Tashkeel.
    Repeat up to 2 times.
    """
    diacritized_result1 = await Runner.run(agent, chunk)
    diacritized_text1 = diacritized_result1.final_output
    reconstructed_diacritized_text, needs_rediacritization = reconstruct_chunk(chunk, diacritized_text1)
    if needs_rediacritization:
        diacritized_result2 = await Runner.run(agent, reconstructed_diacritized_text)
        diacritized_text2 = diacritized_result2.final_output
        reconstructed_diacritized_text, needs_rediacritization = reconstruct_chunk(reconstructed_diacritized_text, diacritized_text2)

    return reconstructed_diacritized_text, needs_rediacritization


async def run_tashkeel_for_chunk(chunk_index: int, chunk: List[Tuple[int, int, str]], agent) -> List[Tuple[int, int, str]]:
    if not chunk:
        return (chunk)

    words = [word for _, _, word in chunk]
    agent_message = ' '.join(words)
    diacritized_text, needs_rediacritization = await run_tashkeel_with_agent(agent_message, agent)
    reconstructed_chunk = [(line_i, word_i, new_word) for (line_i, word_i, word), new_word in zip(chunk, diacritized_text.split())]
    #if needs_rediacritization:
    #    logging.warning(f"""Discrepancy in Tashkeel rewriting after 2 attempts in chunk {chunk_index}.\n
#Original chunk: {agent_message}\n
#Reconstructed chunk: {diacritized_text}
#"""
#        )
    return reconstructed_chunk

async def run_tashkeel(chunks: List[List[Tuple[int, int, str]]]) -> List[List[Tuple[int, int, str]]]:
    new_chunks = []
    agent1 = create_openai_tashkeel_agent()

    #agent2 = create_openai_vowelizer_agent()
    #rewriter_agent = create_rewriter_agent()
    for chunk_i, chunk in enumerate(chunks):
        logging.info(f"Running Tashkeel for chunk {chunk_i + 1}/{len(chunks)}")
        new_chunk = await run_tashkeel_for_chunk(chunk_i, chunk, agent1)
        new_chunks.append(new_chunk)

    #new_chunks = await asyncio.gather(*(run_tashkeel_for_chunk(i, chunk, agent1, agent2, rewriter_agent) for i, chunk in enumerate(chunks)))
    return new_chunks


def parse_args() -> Namespace:
    """Parses command line arguments and returns the parsed arguments."""
    parser = ArgumentParser(description="Source and target files for data")
    parser.add_argument("source", help="Path/filename to the source file containing Arabic text without Tashkeel")
    parser.add_argument("target", help="Path/filename to the target file for saving the output with Tashkeel")
    args = parser.parse_args()
    return args


async def main():
    args = parse_args()
    logging.info("TashkeelAgent: Automated Tashkeel for Arabic text using AI agents")

    with open(args.source, "r") as source_file:
        text = source_file.read()
        lines = text.splitlines()
        logging.info(f"Reading {args.source}: {format(len(lines), ',d')} lines and {format(len(text), ',d')} characters")

    all_words, arabic_words = extract_arabic_words(lines)

    chunks = make_chunks(arabic_words)
    logging.info(f"Splitting text into {len(chunks)} chunks")
    new_chunks = await run_tashkeel(chunks)
    #new_chunks = chunks

    words_dict = defaultdict(defaultdict)
    for chunk in new_chunks:
        for line_i, word_i, word in chunk:
            words_dict[line_i][word_i] = word

    # run_validation_tests(chunks, new_chunks)

    logging.info(f"Merging the chunks back into {len(lines)} lines")

    result = "\n".join([''.join(words_dict[line_i].get(word_i, word)
                                for word_i, word in enumerate(line))
                        for line_i, line in enumerate(all_words)])

    source_line_count = len(lines)
    target_line_count = len(result.splitlines())

    if source_line_count != target_line_count:
        logging.error(f"Unexpected number of lines in final result: {target_line_count} instead of original {source_line_count} lines")

    undiacritized_ratio = get_ratio_of_undiacritized_words(result)

    logging.info(f"Result has {format(undiacritized_ratio, '.2%')} undiacritized words out of {len(arabic_words)} total words")

    logging.info(f"Writing the results to {args.target}")
    with open(args.target, "w") as target_file:
        target_file.write(result)


def run_validation_tests(chunks, new_chunks):
    validated = True
    for i, (chunk, new_chunk) in enumerate(zip(chunks, new_chunks)):
        if normalize_arabic_text(new_chunk) != normalize_arabic_text(chunk):
            validated = False
            logging.error(f"Validation failed for chunk {i+1}: original and annotated version 1 differ")
            logging.error("Original chunk:\n")
            for c in chunk.splitlines():
                print(c)
            logging.error("Annotated chunk 1:\n")
            for c in new_chunk.splitlines():
                print(c)
    if validated:
        logging.info("All validation tests passed")

if __name__ == "__main__":
    asyncio.run(main())
