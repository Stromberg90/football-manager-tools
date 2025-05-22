use byteorder::{LittleEndian, ReadBytesExt};

impl<R: std::io::Read + ?Sized> SiaRead for R {}

pub trait SiaRead: std::io::Read {
    fn read_string(&mut self) -> String {
        let length = self.read_u32::<LittleEndian>().unwrap() as usize;
        let mut buffer = vec![0; length];
        self.read_exact(&mut buffer).unwrap();
        String::from_utf8_lossy(&buffer).to_string()
    }

    fn read_string_u8_len(&mut self) -> String {
        let length = self.read_u8().unwrap() as usize;
        let mut buffer = vec![0; length];
        self.read_exact(&mut buffer).unwrap();
        String::from_utf8_lossy(&buffer).to_string()
    }

    fn read_string_with_length(&mut self, length: usize) -> String {
        let mut buffer = vec![0; length];
        self.read_exact(&mut buffer).unwrap();
        String::from_utf8_lossy(&buffer).to_string()
    }

    fn read_byte_array<const LEN: usize>(&mut self) -> [u8; LEN] {
        let mut values = [0; LEN];
        for i in 0..LEN {
            values[i] = self.read_u8().unwrap();
        }
        values
    }

    fn read_bounding_box(&mut self) -> [f32; 6] {
        let mut values: [f32; 6] = [0f32; 6];
        values[0] = self.read_f32::<LittleEndian>().unwrap();
        values[1] = self.read_f32::<LittleEndian>().unwrap();
        values[2] = self.read_f32::<LittleEndian>().unwrap();
        values[3] = self.read_f32::<LittleEndian>().unwrap();
        values[4] = self.read_f32::<LittleEndian>().unwrap();
        values[5] = self.read_f32::<LittleEndian>().unwrap();
        values
    }
}
