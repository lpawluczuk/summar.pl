# encoding: utf-8

def from_file(file_name):
    """Create raw data from file."""
    # WARNING: IT WILL NOT WORK PROPERLY, IF THERE
    # ARE WHITESPACE CHARACTERS IN OBSERVARTIONS
    # OR LABELS !
    data = []
    words = []
    labels = []

    file = open(file_name)
    for line in file:
        # line = line.strip()
        if len(line.strip()) == 0:
            data.append((words, labels))
            words = []
            labels = []
        else:
            singles, pairs, label = (x.strip() for x in line.split(" | "))
            # line = line.split()
            word = ([x.decode('utf-8') for x in singles.split()],
                    [x.decode('utf-8') for x in pairs.split()])
            # obs_list = [obs.decode('utf-8') for obs in line[:-1]]
            # label = line[-1].decode('utf-8')
            label = label.decode('utf-8')
            words.append(word)
            labels.append(label)

    file.close()
    if len(words) != 0:
        raise Exception("no empty line on the end of the %s file." % file_name)
    return data
