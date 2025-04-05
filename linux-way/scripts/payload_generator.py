import sys
import jsonline_generator


def make_payload_file(filename, output):
    with open(filename, 'r') as infile:
        with open(output, 'w') as outfile:
            for line in infile:
                fields = line.split("|")
                jsonline = jsonline_generator.Jsonline("localhost")
                jsonline.with_tag(fields[0])
                jsonline.with_method(fields[1])
                jsonline.with_uri(fields[2])

                jsonline.add_header("User-Agent", fields[3])
                jsonline.add_header("Content-type", "application/json")
                body = fields[4].strip()
                body = body.replace("\\\\", '\\')
                jsonline.with_body(bytes(body, 'utf-8').decode('unicode_escape'))
                outfile.write(jsonline.toJson())
                outfile.write('\n')


if __name__ == '__main__':
    make_payload_file(sys.argv[1], sys.argv[2])
