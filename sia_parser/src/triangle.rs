use std::cmp::max;

#[derive(Debug)]
pub struct Triangle(pub u16, pub u16, pub u16);

impl Triangle {
    pub fn max(&self) -> u16 {
        max(max(self.0, self.1), self.2)
    }
}
