
def paragraphs(input):
    paragraphs = []

    tmp = input
    while "\n\n" in tmp:
        p = tmp[:tmp.index("\n\n")].strip()
        if p:
            paragraphs.append(p)
        tmp = tmp[tmp.index("\n\n")+len("\n\n"):].strip()
    if tmp:
        paragraphs.append(tmp)
    return paragraphs

def is_header(sentence):
    return not sentence[-1].endswith((".", "?", "!", ";", ":"))