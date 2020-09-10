use std::cmp::max;

#[derive(Debug)]
pub struct Triangle<T>(pub T, pub T, pub T);

impl Triangle<u16> {
    pub fn max(&self) -> u16 {
        max(max(self.0, self.1), self.2)
    }
}

impl Triangle<u32> {
    pub fn max(&self) -> u32 {
        max(max(self.0, self.1), self.2)
    }
}

impl From<Triangle<u16>> for Triangle<u32> {
    fn from(triangle: Triangle<u16>) -> Self {
        Self {
            0: triangle.0.into(),
            1: triangle.1.into(),
            2: triangle.2.into(),
        }
    }
}
