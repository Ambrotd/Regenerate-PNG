
import sys, struct, binascii


#base script https://gist.github.com/sbp/3084622
def get_png_free_data(data): 
    #signature = data[:8]
    data = data[8:]

    while data: 
        length = struct.unpack('>I', data[:4])[0]
        data = data[4:]

        chunk_type = data[:4]
        data = data[4:]

        chunk_data = data[:length]
        data = data[length:]
        if len(chunk_data)  != length:
            #return the real lenght
            return length, chunk_type, chunk_data
        # end of file??
        if len(data) == 0:
            return 0,0,0
        #move the pointer
        data = data[4:]

#calc the new crc and return it 
def calc_crc(chunk_type, chunk_data):
    c = binascii.crc32(chunk_type + chunk_data) & 0xffffffff
    crc = struct.pack('>I', c)
    return crc


# getting the next block
def find_next_block(block_list, length, chunk_type, chunk_data):
    # Calc the bytes missing
    missing_bytes_n = length - len(chunk_data)

    # loop on the block list remember the block is 8192
    for (i,candidate_block) in enumerate(block_list):
        # create new chunk and calc his crc
        full_chunk_data = chunk_data + candidate_block[:missing_bytes_n]
        chunk_crc = candidate_block[missing_bytes_n:missing_bytes_n+4]

        # if the crc is good we go the good one
        if chunk_crc == calc_crc(chunk_type, full_chunk_data):
            block_list.pop(i)
            return candidate_block, block_list

    return None

def find_png_start(block_list):
    # Starting point
    for block in block_list:
        if block[:4] == b"\x89PNG":
            return block

    return None


def main():
    help_msg = sys.argv[0] + " /path/file.png [block size (default: 8192)] [starting_byte(default: start of file)] [stop_byte(default: end of file)]"

    if len(sys.argv) < 2 or len(sys.argv) > 5 or "-h" in sys.argv or "--help" in sys.argv:
        print(help_msg)
        sys.exit(0)

    path = sys.argv[1]
    block_size = int(sys.argv[2]) if len(sys.argv) > 2 else 8192
    start_byte = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    stop_byte = int(sys.argv[4]) if len(sys.argv) > 4 else 0

    blocks = []
    with open(path,"rb") as f:
        dump = f.read()
        for n in range(start_byte, len(dump) if stop_byte == 0 else stop_byte, block_size):
            blocks.append(dump[n:n+block_size])
 

    # Starting block
    data = find_png_start(blocks)
    if data==None:
        print("Png magiv number doesnt exists, bad block size?")
        sys.exit()

    #after we find the header we go for the rest
    while blocks:
        length, chunk_type, chunk_data = get_png_free_data(data)

        # end of the file writing de data to png
        if length==0:
            with open(path+"_regenerated.png","wb") as f:
                f.write(data)
                print("Get your " + path + "_regenerated.png")
                break

        # next block
        next_block, blocks = find_next_block(blocks, length, chunk_type, chunk_data)
        data+=  next_block
    
if __name__== "__main__":
    main()