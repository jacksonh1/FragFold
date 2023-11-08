import math
import numpy as np
import os
import random

def readFastaLines(file):
    header = file.readline().rstrip()
    if header != '' and not header.startswith('>'):
        raise ValueError('Header line in FASTA should begin with >, instead saw:'+header)
    sequence = file.readline().rstrip()
    return header,sequence

def extractSubsequence(sequence,seqRange:tuple):
    # Remember: residue number is 1-indexed, but the sequence is zero-indexed
    return sequence[seqRange[0]-1:seqRange[1]]

def hasGaps(sequence,gapchar:str='-'):
    # search for gaps within the sequence (between non-gap chars)
    return sum([x for x in map(lambda x: 1 if x != '' else 0,sequence.split(gapchar))]) > 1

def hasLower(sequence):
    for a in sequence:
        if a.islower():
            return True
    return False

def countLower(sequence):
    count = 0
    for a in sequence:
        if a.islower():
            count+=1
    return count

def calcHammingDistance(s1,s2):
    assert len(s1) == len(s2)
    return np.sum([a!=b for a,b in zip(s1,s2)])

def shuffleSeq(seq,maxPercentIdentity=0.3):
    assert len(seq) > 1
    minHammingDistance = math.floor((1-maxPercentIdentity)*len(seq))
    hammingDistance = None
    shuffled_seq = None
    while hammingDistance is None or hammingDistance < minHammingDistance:
        seq_list = list(seq)
        random.shuffle(seq_list)
        shuffled_seq = ''.join(seq_list)
        hammingDistance = calcHammingDistance(shuffled_seq,seq)
        # print(shuffled_seq,hammingDistance)
    return shuffled_seq

def createMSA(inputMSA: str, protein_range: tuple, fragment_range: tuple, subsample: int, a3m_output_path: str,
              protein_copies: int = 1, fragment_single_sequence=False, fragment_shuffle=False):
    full_query_seq = ''
    new_info_line = ''

    with open(inputMSA,'r') as input_file, open(a3m_output_path,'w') as output_file:
        info_line = input_file.readline().rstrip()
        # print('info line:',info_line)
        if not info_line.startswith('#'):
            raise ValueError('File should begin with #, instead saw'+info_line)
            
        # First line is whole protein sequence
        header,whole_sequence = readFastaLines(input_file)
        query_protein_sequence = extractSubsequence(whole_sequence,protein_range)
        query_fragment_sequence = extractSubsequence(whole_sequence,fragment_range)
        if fragment_shuffle:
            query_fragment_sequence = shuffleSeq(query_fragment_sequence)
        full_query_seq = query_protein_sequence + query_fragment_sequence
        new_info_line = f"#{len(query_protein_sequence)},{len(query_fragment_sequence)}\t{protein_copies},1"+'\n'
        
        output_file.write(new_info_line)
        output_file.write('>101\t102\n')
        output_file.write(full_query_seq+'\n')
            
        count = 1
        # Remaining lines are the matches from the MSA
        while header != '':
            header,sequence = readFastaLines(input_file)
            if subsample > 0 and count == subsample:
                break
            
            # Get the protein/fragment sequence
            protein_sequence = extractSubsequence(sequence,protein_range)
            fragment_sequence = extractSubsequence(sequence,fragment_range)

            if protein_sequence.replace('-','') != '':
                new_header = header + '\t101\n'
                new_protein_sequence = protein_sequence.ljust(len(full_query_seq),'-') 
                new_protein_sequence = new_protein_sequence + '-'*countLower(protein_sequence) + '\n'
                output_file.write(new_header)
                output_file.write(new_protein_sequence)
            if fragment_sequence.replace('-','') != '' and not hasGaps(fragment_sequence) and not (fragment_single_sequence or fragment_shuffle):
                new_header = header + '\t102\n'
                new_fragment_sequence = fragment_sequence.rjust(len(full_query_seq),'-')
                new_fragment_sequence = new_fragment_sequence + '-'*countLower(fragment_sequence) + '\n'
                output_file.write(new_header)
                output_file.write(new_fragment_sequence)
            count+=1

def createMSAHeteromicInteraction(fullLengthProteinMSA: str, protein_range: tuple, fragmentProteinMSA: str, fragment_range: tuple, subsample: int, a3m_output_path: str, protein_copies: int = 1,
                                  fragmentSingleSequence=False, fragmentShuffle=False):
    full_query_seq = ''
    new_info_line = ''

    with open(fullLengthProteinMSA,'r') as fulllength_input_file, open(fragmentProteinMSA,'r') as fragment_input_file, open(a3m_output_path,'w') as output_file:
        info_line = fulllength_input_file.readline().rstrip()
        if not info_line.startswith('#'):
            raise ValueError(f"{fullLengthProteinMSA} should begin with #, instead saw'+info_line")
        info_line = fragment_input_file.readline().rstrip()
        if not info_line.startswith('#'):
            raise ValueError(f"{fragmentProteinMSA} should begin with #, instead saw'+info_line")
            
        # First line in the full-length msa is whole protein sequence
        fulllength_header,whole_sequence = readFastaLines(fulllength_input_file)
        query_protein_sequence = extractSubsequence(whole_sequence,protein_range)
        # First line in fragment msa is the whole sequence of the protein that was broken into fragments
        fragment_header,whole_fragmented_sequence = readFastaLines(fragment_input_file)
        query_fragment_sequence = extractSubsequence(whole_fragmented_sequence,fragment_range)
        if fragmentShuffle:
            query_fragment_sequence = shuffleSeq(query_fragment_sequence)
        full_query_seq = query_protein_sequence + query_fragment_sequence
        new_info_line = f"#{len(query_protein_sequence)},{len(query_fragment_sequence)}\t{protein_copies},1"+'\n'
        
        output_file.write(new_info_line)
        output_file.write('>101\t102\n')
        output_file.write(full_query_seq+'\n')
            
        # Remaining lines are the matches from the MSAs
        # First get full-length MSA entries
        count = 1
        while fulllength_header != '':
            fulllength_header,sequence = readFastaLines(fulllength_input_file)
            if subsample > 0 and count == subsample:
                break
            # Get the protein/fragment sequence
            protein_sequence = extractSubsequence(sequence,protein_range)
            if protein_sequence.replace('-','') != '':
                new_header = fulllength_header + '\t101\n'
                new_protein_sequence = protein_sequence.ljust(len(full_query_seq),'-') 
                new_protein_sequence = new_protein_sequence + '-'*countLower(protein_sequence) + '\n'
                output_file.write(new_header)
                output_file.write(new_protein_sequence)
            count+=1
        # Next get fragment MSA entries
        count = 1
        while fragment_header != '' and not (fragmentSingleSequence or fragmentShuffle):
            fragment_header,sequence = readFastaLines(fragment_input_file)
            if subsample > 0 and count == subsample:
                break
            # Get the protein/fragment sequence
            fragment_sequence = extractSubsequence(sequence,fragment_range)
            if fragment_sequence.replace('-','') != '' and not hasGaps(fragment_sequence):
                new_header = fragment_header + '\t102\n'
                new_fragment_sequence = fragment_sequence.rjust(len(full_query_seq),'-')
                if fragmentShuffle:
                    new_fragment_sequence = shuffleSeq(new_fragment_sequence)
                new_fragment_sequence = new_fragment_sequence + '-'*countLower(fragment_sequence) + '\n'
                output_file.write(new_header)
                output_file.write(new_fragment_sequence)
            count+=1
        
def createIndividualMSAsFullLengthFragment(a3m_path,name,protein_range,fragment_start_range,fragment_length,protein_copies=1):
    '''Loads a monomer MSA and creates new MSAs that contain 1) a large section of the monomer and 2) a short fragment of the monomer
    
    Args
    ----
    a3m_path : str
        path to an a3m formatted msa file describing the monomeric protein (obtained from colab_mmseqs)
    name : str
        name of the monomeric protein
    protein_range : list
        an inclusive range defining which positions of the MSA to take from the monomeric protein (sometimes the ends need to be chopped off)
    fragment_start_range : list
        an inclusive range defining the range of starting residues for fragments of length `fragment_length`
    fragment_length : int
        the number of residues to take when defining a fragment
    '''
    dir_name = f"{name}{protein_copies}copies_tile{str(fragment_length)}aa"
    try:
        os.makedirs(dir_name, exist_ok=False)
    except FileExistsError:
        print('Directory already exists, possibly overwriting existing files')
            
    for fragment_start in range(fragment_start_range[0],fragment_start_range[1]-fragment_length+2):
        fragment_range = (fragment_start,fragment_start+fragment_length-1) # range is inclusive
        a3m_out_path = f"{dir_name}/{name}{protein_copies}copies_{protein_range[0]}-{protein_range[1]}_{name}_{fragment_range[0]}-{fragment_range[1]}.a3m"
        createMSA(a3m_path, protein_range, fragment_range, -1, a3m_out_path, protein_copies)
        
def createIndividualMSAsFullLengthFragmentHeteromeric(fulllength_a3m_path,fulllength_name,fragment_a3m_path,fragment_name,protein_range,fragment_start_range,fragment_length,protein_copies=1):
    '''Loads a monomer MSA and creates new MSAs that contain 1) a large section of the monomer and 2) a short fragment of the monomer
    
    Args
    ----
    fulllength_a3m_path : str
        path to an a3m formatted msa file describing the monomeric protein (obtained from colab_mmseqs)    
    fragment_a3m_path : str
        path to an a3m formatted msa file describing the protein broken into fragments (obtained from colab_mmseqs)
    name : str
        name of the monomeric protein
    protein_range : list
        an inclusive range defining which positions of the MSA to take from the monomeric protein (sometimes the ends need to be chopped off)
    fragment_start_range : list
        an inclusive range defining the range of starting residues for fragments of length `fragment_length`
    fragment_length : int
        the number of residues to take when defining a fragment
    '''
    dir_name = f"{fulllength_name}{protein_copies}copies_{fragment_name}tile{str(fragment_length)}aa"
    try:
        os.makedirs(dir_name, exist_ok=False)
    except FileExistsError:
        print('Directory already exists, possibly overwriting existing files')
            
    for fragment_start in range(fragment_start_range[0],fragment_start_range[1]-fragment_length+2):
        fragment_range = (fragment_start,fragment_start+fragment_length-1) # range is inclusive
        a3m_out_path = f"{dir_name}/{fulllength_name}{protein_copies}copies_{protein_range[0]}-{protein_range[1]}_{fragment_name}_{fragment_range[0]}-{fragment_range[1]}.a3m"
        createMSAHeteromicInteraction(fulllength_a3m_path, protein_range, fragment_a3m_path, fragment_range, -1, a3m_out_path, protein_copies)