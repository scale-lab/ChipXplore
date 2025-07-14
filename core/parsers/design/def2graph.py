#### from @ahmed-agiza
import os
import pickle
import argparse
import multiprocessing as mp
import networkx as nx
import openroad  as odb


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Generate graph representations from LEF/DEF files"
    )
    parser.add_argument(
        "-l",
        "--lef",
        type=str,
        required=True,
        help="Path to the LEF file",
    )
    parser.add_argument(
        "-i",
        "--input",
        type=str,
        required=True,
        help="Directory containing input DEF files",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="output/",
        help="Directory for output files",
    )
    parser.add_argument(
        "-f",
        "--force-overwrite",
        action="store_true",
        help="Overwrite existing files in output directory",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable detailed output messages"
    )
    parser.add_argument(
        "-s",
        "--skip-processed",
        action="store_true",
        help="Skip previously processed files",
    )
    parser.add_argument(
        "-g",
        "--generate-pickle",
        action="store_true",
        help="Generate graph pickle  output",
    )
    parser.add_argument(
        "-d", "--generate-dot", action="store_true", help="Generate graph DOT file"
    )
    parser.add_argument(
        "-j",
        "--jobs",
        type=int,
        default=2,
        help="Number of parallel jobs to run (default: 2, use 0 for max)",
    )
    return parser.parse_args()


def validate_directories(input_dir, output_dir, force_overwrite, skip_processed):
    if not os.path.isdir(input_dir):
        raise ValueError("Input directory does not exist")

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    elif not os.path.isdir(output_dir):
        raise ValueError(f"Output directory {output_dir} is not a directory")
    elif os.listdir(output_dir) and not force_overwrite and not skip_processed:
        raise ValueError(
            f"Output directory {output_dir} is not empty. Use --force-overwrite to overwrite existing files or --skip-processed to skip previously processed files"
        )


def generate_graph(design, args):
    try:
        def_file = f"{design}.def"
        pickle_file = os.path.join(args.output, f"{os.path.basename(design)}.graph.pkl")
        dot_file = os.path.join(args.output, f"{os.path.basename(design)}.graph.dot")

        if args.skip_processed and (
            (
                args.generate_pickle
                and args.generate_dot
                and os.path.exists(pickle_file)
                and os.path.exists(dot_file)
            )
            or (
                args.generate_pickle
                and not args.generate_dot
                and os.path.exists(pickle_file)
            )
            or (
                not args.generate_pickle
                and args.generate_dot
                and os.path.exists(dot_file)
            )
        ):
            return 1
        db = odb.dbDatabase.create()
        odb.read_lef(db, args.lef) 
        odb.read_def(db, def_file)
        block = db.getChip().getBlock()
        g = create_graph(block)

        if args.verbose:
            print(f"Num nodes: {len(g.nodes())}")
            print(f"Num edges: {len(g.edges())}")
            print("========================")

        if args.generate_pickle:
            with open(pickle_file, "wb") as f:
                pickle.dump(g, f, pickle.HIGHEST_PROTOCOL)
        if args.generate_dot:
            nx.nx_pydot.write_dot(g, dot_file)

    except Exception as e:
        print(f"Error processing {design}: {str(e)}")
        return 0
    return 1


def create_graph(block):
    g = nx.DiGraph()

    add_net_connections(g, block)
    add_internal_connections(g, block)

    return g


def add_net_connections(g, block):
    for term in block.getITerms():
        net = term.getNet()
        if net.getSigType() == 'POWER' or net.getSigType() == 'GROUND':
            continue 
        if not net:
            continue
        bterm_drvr = net.get1stBTerm()
        if bterm_drvr:
            g.add_edge(
                bterm_drvr.getName(), get_pin_name(term), type="net", block="True"
            )
            nx.set_node_attributes(
                g, {bterm_drvr.getName(): bterm_drvr.getIoType()}, name="direction"
            )
        else:
            drvr = net.getFirstOutput()
            g.add_edge(
                get_pin_name(drvr), get_pin_name(term), type="net", block="False"
            )
            nx.set_node_attributes(
                g,
                {
                    get_pin_name(drvr): drvr.getIoType(),
                    get_pin_name(term): term.getIoType(),
                },
                name="direction",
            )


def add_internal_connections(g, block):
    for inst in block.getInsts():
        in_terms = [t for t in inst.getITerms() if t.getIoType() == "INPUT"]
        out_terms = [t for t in inst.getITerms() if t.getIoType() == "OUTPUT"]

        for tout in out_terms:
            for tin in in_terms:
                add_edge_attributes(g, tin, tout)


def add_edge_attributes(g, tin, tout):
    tin_name, tout_name = get_pin_name(tin), get_pin_name(tout)
    g.add_edge(tin_name, tout_name, type="internal", block="False")

    node_attributes = {
        tin_name: {
            "direction": tin.getIoType(),
            "cell": tin.getInst().getMaster().getName(),
        },
        tout_name: {
            "direction": tout.getIoType(),
            "cell": tout.getInst().getMaster().getName(),
        },
    }

    for node, attrs in node_attributes.items():
        nx.set_node_attributes(g, {node: attrs})


def get_pin_name(iterm):
    return f"{iterm.getInst().getName()}/{iterm.getMTerm().getName()}"


def main():
    args = parse_arguments()
    validate_directories(
        args.input, args.output, args.force_overwrite, args.skip_processed
    )

    designs = [
        os.path.join(args.input, m[:-4])
        for m in os.listdir(args.input)
        if m.endswith(".def")
    ]

    pool = mp.Pool(mp.cpu_count() if args.jobs == 0 else args.jobs)
    for i, design in enumerate(designs, 1):
        if args.verbose:
            print(f"Processing {design} ({i}/{len(designs)})")
        pool.apply_async(generate_graph, (design, args))
    pool.close()
    pool.join()


if __name__ == "__main__":
    main()