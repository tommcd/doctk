//! Native CLI harness for the spike: reads Markdown on stdin, prints results.
//!
//! Used by `check_against_doctk.py` to compare this Rust implementation
//! against the Python oracle (doctk) — the same "shell out and diff JSON"
//! pattern as tests/e2e/test_ts_scanner_conformance.py.
//!
//!   echo "# Hi" | doctk-spike scan
//!   echo "..."  | doctk-spike promote <node_id>

use std::io::Read;
use std::process::exit;

fn main() {
    let args: Vec<String> = std::env::args().collect();

    let mut input = String::new();
    if std::io::stdin().read_to_string(&mut input).is_err() {
        eprintln!("error: could not read stdin");
        exit(2);
    }

    match args.get(1).map(String::as_str) {
        Some("scan") => {
            let headings = doctk_spike::scan_headings(&input);
            println!("{}", serde_json::to_string(&headings).unwrap());
        }
        Some("promote") => {
            let Some(node_id) = args.get(2) else {
                eprintln!("usage: doctk-spike promote <node_id>");
                exit(2);
            };
            match doctk_spike::promote(&input, node_id) {
                Ok(text) => print!("{text}"),
                Err(err) => {
                    eprintln!("{err}");
                    exit(1);
                }
            }
        }
        _ => {
            eprintln!("usage: doctk-spike <scan|promote NODE_ID>");
            exit(2);
        }
    }
}
