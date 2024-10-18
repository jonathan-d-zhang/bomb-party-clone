use std::fs::OpenOptions;
use std::io::Write;
use std::iter;

use itertools::Itertools;
use rayon::prelude::*;
use serde::Serialize;

const ALPHABET: &'static str = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";

#[derive(Serialize, Debug)]
struct Infix {
    infix: String,
    wpp: usize,
    words: Vec<String>,
}

fn main() {
    let words = include_str!("../dict.txt").split_whitespace().collect_vec();

    let out: Vec<_> = (2..3 + 1)
        .map(|length| iter::repeat(ALPHABET).take(length).map(|s| s.chars()))
        .flat_map(|l| l.multi_cartesian_product())
        .par_bridge()
        .filter_map(|infix| {
            let needle = infix.iter().join("");

            let matched = words
                .iter()
                .filter(|w| w.contains(&needle))
                .map(|w| w.to_string())
                .collect_vec();

            let i = Infix {
                infix: needle,
                wpp: matched.len(),
                words: matched,
            };
            if i.wpp >= 10 {
                Some(i)
            } else {
                None
            }
        })
        .collect();

    let j = serde_json::to_string(&out).unwrap();

    let mut file = OpenOptions::new()
        .write(true)
        .create(true)
        .open("ist.json")
        .unwrap();
    file.write(j.as_bytes()).unwrap();
}
