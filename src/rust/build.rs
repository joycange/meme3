use std::env;
use std::process::Command;

fn main() {
    // FIXME: maybe pyo3-build-config should provide a way to do this?
    let python = env::var("PYO3_PYTHON").unwrap_or("python3".to_string());
    let output = Command::new(&python)
        .env("PYTHONPATH", "../")
        .arg("../_cffi_src/build_openssl.py")
        .output()
        .expect("failed to execute build_openssl.py");
    let stdout = String::from_utf8(output.stdout).unwrap();
    let mut include = String::new();
    for line in stdout.lines() {
        if line.starts_with("cargo:") {
            println!("{}", line);
        } else if line.starts_with("include:") {
            include = line.replace("include:", "");
        }
    }
    let openssl_include =
        std::env::var_os("DEP_OPENSSL_INCLUDE").expect("unable to find openssl include path");
    cc::Build::new()
        .file("_openssl.c")
        .include(include)
        .include(openssl_include)
        .compile("_openssl.a");
}
