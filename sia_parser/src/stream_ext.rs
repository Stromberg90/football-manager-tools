use crate::{bounding_box::BoundingBox, triangle::Triangle};
use byteorder::{LittleEndian, ReadBytesExt};
use io::{Read, Seek, SeekFrom};
use nalgebra::{Vector2, Vector3};
use std::str::Utf8Error;
use std::{fs::File, io, str};

pub trait StreamExt {
    fn skip(&mut self, num_bytes: i64);
    fn position(&mut self) -> io::Result<u64>;
    fn read_vector2(&mut self) -> Vector2<f32>;
    fn read_vector3(&mut self) -> Vector3<f32>;
    fn read_bounding_box(&mut self) -> BoundingBox;
    fn read_string(&mut self) -> Result<String, Utf8Error>;
    fn read_string_u8_len(&mut self) -> Result<String, Utf8Error>;
}

pub(crate) trait ReadTriangle<T> {
    fn read_triangle(&mut self) -> Triangle<T>;
}

impl ReadTriangle<u16> for File {
    fn read_triangle(&mut self) -> Triangle<u16> {
        Triangle(
            self.read_u16::<LittleEndian>().unwrap(),
            self.read_u16::<LittleEndian>().unwrap(),
            self.read_u16::<LittleEndian>().unwrap(),
        )
    }
}

impl ReadTriangle<u32> for File {
    fn read_triangle(&mut self) -> Triangle<u32> {
        Triangle(
            self.read_u32::<LittleEndian>().unwrap(),
            self.read_u32::<LittleEndian>().unwrap(),
            self.read_u32::<LittleEndian>().unwrap(),
        )
    }
}

impl StreamExt for File {
    fn skip(&mut self, num_bytes: i64) {
        self.seek(SeekFrom::Current(num_bytes)).unwrap();
    }
    fn position(&mut self) -> Result<u64, std::io::Error> {
        self.seek(SeekFrom::Current(0))
    }

    fn read_vector2(&mut self) -> Vector2<f32> {
        let x = self.read_f32::<LittleEndian>().unwrap();
        let y = self.read_f32::<LittleEndian>().unwrap();
        Vector2::new(x, y)
    }

    fn read_vector3(&mut self) -> Vector3<f32> {
        let x = self.read_f32::<LittleEndian>().unwrap();
        let y = self.read_f32::<LittleEndian>().unwrap();
        let z = self.read_f32::<LittleEndian>().unwrap();
        Vector3::new(x, y, z)
    }

    fn read_bounding_box(&mut self) -> BoundingBox {
        BoundingBox {
            min_x: self.read_f32::<LittleEndian>().unwrap(),
            min_y: self.read_f32::<LittleEndian>().unwrap(),
            min_z: self.read_f32::<LittleEndian>().unwrap(),
            max_x: self.read_f32::<LittleEndian>().unwrap(),
            max_y: self.read_f32::<LittleEndian>().unwrap(),
            max_z: self.read_f32::<LittleEndian>().unwrap(),
        }
    }

    fn read_string(&mut self) -> Result<String, Utf8Error> {
        let string_length = self.read_u32::<LittleEndian>().unwrap();
        let mut string_buf = vec![0u8; string_length as usize];

        self.read_exact(&mut string_buf).unwrap();
        Ok(str::from_utf8(&string_buf)?.to_owned())
    }

    fn read_string_u8_len(&mut self) -> Result<String, Utf8Error> {
        let string_length = self.read_u8().unwrap();
        let mut string_buf = vec![0u8; string_length as usize];

        self.read_exact(&mut string_buf).unwrap();
        Ok(str::from_utf8(&string_buf)?.to_owned())
    }
}
