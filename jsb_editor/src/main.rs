use std::{fs, path::Path, string::String};

use byteorder::{ByteOrder, LittleEndian};

#[derive(Debug, PartialEq)]
enum Value {
    String(String),
    Unknown(u8),
}

enum ValueType {
    RenderFlags = 2,
    VariableLength = 8,
    Index = 74,
    BodyPart = 88,
    RearCap = 152,
    Glasses = 136,
    OfficeSmall = 216,
    OfficeMedium = 232,
    LargeBoardroom = 248,
    Unknown = 0,
}

impl From<u8> for ValueType {
    fn from(n: u8) -> Self {
        match n {
            0 => Self::Unknown,
            2 => Self::RenderFlags,
            8 => Self::VariableLength,
            74 => Self::Index,
            88 => Self::BodyPart,
            152 => Self::RearCap,
            136 => Self::Glasses,
            216 => Self::OfficeSmall,
            232 => Self::OfficeMedium,
            248 => Self::LargeBoardroom,
            _ => Self::Unknown,
        }
    }
}

struct Parser {
    index: usize,
    buffer: Vec<u8>,
}

impl Parser {
    fn from_file<P: AsRef<Path>>(path: P) -> Parser {
        Parser {
            index: 0,
            buffer: fs::read(path).unwrap(),
        }
    }

    fn parse(&mut self) {
        self.index = 0;
        while self.index < self.buffer.len() {
            dbg!(self.read_key());
            if let Value::Unknown(v) = dbg!(self.read_value()) {
                panic!("Unknown value {v}");
            }
        }
    }

    fn read_key(&mut self) -> String {
        let string_length = self.buffer[self.index] as usize;
        self.index += 1;
        let key = String::from_utf8_lossy(&self.buffer[self.index..self.index + string_length])
            .to_string();
        self.index += string_length;
        key
    }

    fn read_value(&mut self) -> Value {
        let u8 = self.buffer[self.index];
        let kind: ValueType = u8.into();
        self.index += 1;
        match kind {
            ValueType::VariableLength => {
                let length =
                    LittleEndian::read_u32(&self.buffer[self.index..self.index + 4]) as usize;
                self.index += 4;
                let string = String::from_utf8_lossy(&self.buffer[self.index..self.index + length])
                    .to_string();
                self.index += length;
                Value::String(string)
            }
            ValueType::OfficeSmall => {
                let length = 12;
                let string = String::from_utf8_lossy(&self.buffer[self.index..self.index + length])
                    .to_string();
                self.index += length;
                Value::String(string)
            }
            ValueType::OfficeMedium => {
                let length = 13;
                let string = String::from_utf8_lossy(&self.buffer[self.index..self.index + length])
                    .to_string();
                self.index += length;
                Value::String(string)
            }
            ValueType::LargeBoardroom => {
                let length = 14;
                let string = String::from_utf8_lossy(&self.buffer[self.index..self.index + length])
                    .to_string();
                self.index += length;
                Value::String(string)
            }
            _ => Value::Unknown(u8),
        }
    }
}

fn main() {    
    Parser::from_file(
        r#"D:\FM24Data\sigraphics-pc\shaders\dx11\room_assets.jsb"#,
    )
    .parse();
}
