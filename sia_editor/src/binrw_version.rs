#[derive(
    BinRead,
    // BinWrite,
    Debug,
)]
#[br(little, magic = b"SHSM")]
struct SiaFile {
    version_maybe: u32,
    name: SiaString,
    _unknown1: [u8; 12],
    _maybe_scale: f32,
    bounding_box: [f32; 6],
    objects_num: u32,
    #[br(parse_with = custom_parser)]
    meshes: Vec<SiaMesh>,
    meshes_num: u32,
}

#[derive(BinRead, Debug)]
struct SiaMesh {
    _vertex_offset: [u8; 4],
    vertices_num: u32,
    _triangle_offset: [u8; 4],
    triangles_num: u32,
    id: u32,
    _unknown: [u8; 8],
}

#[binrw::parser(reader, endian)]
fn custom_parser() -> BinResult<Vec<SiaMesh>> {
    let mut values = Vec::new();
    // map.insert(
    //     <_>::read_options(reader, endian, ())?,
    //     <_>::read_options(reader, endian, ())?,
    // );
    Ok(values)
}

#[derive(Debug)]
struct SiaString(String);

impl BinRead for SiaString {
    type Args<'a> = ();

    fn read_options<R: Read + std::io::Seek>(
        reader: &mut R,
        endian: binrw::Endian,
        (): Self::Args<'_>,
    ) -> binrw::BinResult<Self> {
        let mut string = String::new();
        let length = <u32>::read_options(reader, endian, ())?;
        for _ in 0..length {
            let val = <u8>::read_options(reader, endian, ())?;
            string.push(val as char);
        }
        Ok(Self(string))
    }
}

impl BinWrite for SiaString {
    type Args<'a> = ();

    fn write_options<W: Write + std::io::Seek>(
        &self,
        writer: &mut W,
        endian: binrw::Endian,
        args: Self::Args<'_>,
    ) -> binrw::BinResult<()> {
        (self.0.len() as u32).write_options(writer, endian, args)?;
        self.0.as_bytes().write_options(writer, endian, args)?;

        Ok(())
    }
}
