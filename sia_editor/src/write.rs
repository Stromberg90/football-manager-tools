use byteorder::{LittleEndian, WriteBytesExt};

pub(crate) fn write_string(mut bytes: impl std::io::Write, text: &str) {
    bytes.write_u32::<LittleEndian>(text.len() as u32).unwrap();
    bytes.write_all(text.as_bytes()).unwrap();
}

pub(crate) fn write_string_u8_len(mut bytes: impl std::io::Write, text: &str) {
    bytes.write_u8(text.len() as u8).unwrap();
    bytes.write_all(text.as_bytes()).unwrap();
}
