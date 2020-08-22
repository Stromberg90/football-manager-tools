use byteorder::{LittleEndian, ReadBytesExt};
use nalgebra::{Vector2, Vector3};
use std::fs::File;
use std::io::Seek;
use std::io::{Read, Write};
use std::path::{Path, PathBuf};
use std::str;

#[derive(Debug)]
pub struct Vertex {
    pub position: Vector3<f32>,
    pub uv: Vector2<f32>,
    pub normals: Vector3<f32>,
}

#[derive(Debug)]
pub struct Triangle(pub u16, pub u16, pub u16);

#[derive(Debug)]
pub struct Texture {
    name: String,
    id: u8,
}

#[derive(Debug)]
pub struct Material {
    pub name: String,
    pub kind: String,
    pub textures_num: u8,
    pub textures: Vec<Texture>,
}

impl Material {
    fn new() -> Self {
        Material {
            name: String::new(),
            kind: String::new(),
            textures_num: 0,
            textures: Vec::new(),
        }
    }
}

#[derive(Debug)]
pub struct BoundingBox {
    pub max_x: f32,
    pub max_y: f32,
    pub max_z: f32,
    pub min_x: f32,
    pub min_y: f32,
    pub min_z: f32,
}

impl BoundingBox {
    fn new() -> Self {
        BoundingBox {
            max_x: 0f32,
            max_y: 0f32,
            max_z: 0f32,
            min_x: 0f32,
            min_y: 0f32,
            min_z: 0f32,
        }
    }
}

#[derive(Debug)]
pub struct Mesh {
    pub materials_num: u8,
    pub materials: Vec<Material>,
}

impl Mesh {
    fn new() -> Self {
        Mesh {
            materials_num: 0,
            materials: Vec::new(),
        }
    }
}

#[derive(Debug)]
pub struct Model {
    pub unknown0: [u8; 12],
    pub who_knows: f32,
    pub objects_num: u32,
    pub object_id: u32,
    pub something_about_faces_or_vertices: u32,
    pub unknown: [u8; 4],
    pub unknown2: [u8; 8],
    pub unknown3: [u8; 16],
    pub unknown4: [u8; 24],
    pub unknown4a: [u8; 24],
    pub unknown4b: [u8; 16],
    pub unknown5: u32,
    pub maybe_version: u32,
    pub name: String,
    pub bounding_box: BoundingBox,
    pub num_vertices: u32,
    pub num_meshes: u32,
    pub meshes: Vec<Mesh>,
    pub vertices: Vec<Vertex>,
    pub triangles: Vec<Triangle>,
}

impl Model {
    fn new() -> Self {
        Model {
            unknown0: [0u8; 12],
            who_knows: 0f32,
            objects_num: 0,
            object_id: 0,
            something_about_faces_or_vertices: 0,
            unknown: [0u8; 4],
            unknown2: [0u8; 8],
            unknown3: [0u8; 16],
            unknown4: [0u8; 24],
            unknown4a: [0u8; 24],
            unknown4b: [0u8; 16],
            unknown5: 0,
            maybe_version: 0,
            name: String::new(),
            bounding_box: BoundingBox::new(),
            num_vertices: 0,
            num_meshes: 0,
            meshes: Vec::new(),
            vertices: Vec::new(),
            triangles: Vec::new(),
        }
    }
}

fn read_string(file: &mut File) -> String {
    let string_length = file.read_u32::<LittleEndian>().unwrap();
    let mut string_buf = Vec::<u8>::with_capacity(string_length as usize);
    for _ in 0..string_length {
        string_buf.push(0);
    }

    file.read_exact(&mut string_buf).unwrap();
    str::from_utf8(&string_buf).unwrap().to_owned()
}

pub fn parse<P: AsRef<Path>>(filepath: P) -> Model {
    dbg!(filepath.as_ref());
    let mut file = File::open(filepath).unwrap();

    let mut model = Model::new();

    let mut begin_file_tag = [0u8; 4];
    file.read_exact(&mut begin_file_tag).unwrap();
    let begin_file_tag = str::from_utf8(&begin_file_tag).unwrap();
    if begin_file_tag != "SHSM" {
        panic!("Expexted header SHSM, but found {}", begin_file_tag);
    }

    model.maybe_version = file.read_u32::<LittleEndian>().unwrap();

    model.name = read_string(&mut file);

    // So far these bytes have only been zero,
    // changing them did nothing
    model.unknown0 = [0u8; 12];
    file.read_exact(&mut model.unknown0).unwrap();

    // This might be some sort of scale, since it tends to resemble another bouding box value
    // changing it did nothing
    model.who_knows = file.read_f32::<LittleEndian>().unwrap();

    model.bounding_box.min_x = file.read_f32::<LittleEndian>().unwrap();
    model.bounding_box.min_y = file.read_f32::<LittleEndian>().unwrap();
    model.bounding_box.min_z = file.read_f32::<LittleEndian>().unwrap();

    model.bounding_box.max_x = file.read_f32::<LittleEndian>().unwrap();
    model.bounding_box.max_y = file.read_f32::<LittleEndian>().unwrap();
    model.bounding_box.max_z = file.read_f32::<LittleEndian>().unwrap();

    model.objects_num = file.read_u32::<LittleEndian>().unwrap();
    dbg!(&model.objects_num);

    // So far has been 0's, when I changed it the mesh became invisible
    model.unknown = [0u8; 4];
    file.read_exact(&mut model.unknown).unwrap();

    model.num_vertices = file.read_u32::<LittleEndian>().unwrap();
    // Zero's, changing it made it invisible
    model.unknown5 = file.read_u32::<LittleEndian>().unwrap();

    // This diveded by 3 gives the amount of faces, like another set of bytes later on
    // I'm wondering if this is the total amount of faces, and the other one is per mesh
    model.something_about_faces_or_vertices = file.read_u32::<LittleEndian>().unwrap();

    // This needs to be moved into the mesh, then maybe when reading faces/vertices/materials one can match against it.
    model.object_id = file.read_u32::<LittleEndian>().unwrap();

    dbg!(&model.object_id);
    // Changing these did nothing
    model.unknown2 = [0u8; 8];
    file.read_exact(&mut model.unknown2).unwrap();
    dbg!(model.unknown2);

    model.num_meshes = file.read_u32::<LittleEndian>().unwrap();
    dbg!(file.seek(std::io::SeekFrom::Current(0)));
    dbg!(model.num_meshes);

    // Changing these did nothing
    model.unknown3 = [0u8; 16];
    file.read_exact(&mut model.unknown3).unwrap();

    for _ in 0..model.num_meshes {
        let mut mesh = Mesh::new();
        let material_kind = read_string(&mut file);
        mesh.materials_num = file.read_u8().unwrap();
        for _ in 0..mesh.materials_num {
            let mut material = Material::new();
            material.kind = material_kind.to_owned();
            material.name = read_string(&mut file);
            material.textures_num = file.read_u8().unwrap();
            for _ in 0..material.textures_num {
                let uknown = file.read_u8().unwrap(); //Maybe a way to identify which texture it is, like a id
                let texture = Texture {
                    name: read_string(&mut file),
                    id: uknown,
                };
                material.textures.push(texture);
            }
            mesh.materials.push(material);
        }
        model.meshes.push(mesh);
    }

    model.unknown4 = [0u8; 24];
    file.read_exact(&mut model.unknown4).unwrap();
    model.unknown4a = [0u8; 24];
    file.read_exact(&mut model.unknown4a).unwrap();
    model.unknown4b = [0u8; 16];
    file.read_exact(&mut model.unknown4b).unwrap();

    // Maybe this is for this mesh, and the earlier one is for the entire file.
    let local_num_vertecies = file.read_u32::<LittleEndian>();

    let maybe_a_identifer_num = file.read_u32::<LittleEndian>();

    for _ in 0..model.num_vertices {
        let pos_x = file.read_f32::<LittleEndian>().unwrap();
        let pos_y = file.read_f32::<LittleEndian>().unwrap();
        let pos_z = file.read_f32::<LittleEndian>().unwrap();

        // Think these are normals, when plotted out as vertices, they make a sphere.
        // Which makes sense if it's normals
        let normal_x = file.read_f32::<LittleEndian>().unwrap();
        let normal_y = file.read_f32::<LittleEndian>().unwrap();
        let normal_z = file.read_f32::<LittleEndian>().unwrap();
        println!("Normals");
        println!("\t{}", normal_x);
        println!("\t{}", normal_y);
        println!("\t{}", normal_z);

        let uv_x = file.read_f32::<LittleEndian>().unwrap();
        let uv_y = file.read_f32::<LittleEndian>().unwrap();

        println!("Unknowns");
        // Thinking these are tangents or binormals, last one is always 1 or -1
        println!("\t{}", file.read_f32::<LittleEndian>().unwrap());
        println!("\t{}", file.read_f32::<LittleEndian>().unwrap());
        println!("\t{}", file.read_f32::<LittleEndian>().unwrap());
        println!("\t{}", file.read_f32::<LittleEndian>().unwrap());

        model.vertices.push(Vertex {
            position: Vector3::new(pos_x, pos_y, pos_z),
            uv: Vector2::new(uv_x, uv_y),
            normals: Vector3::new(normal_x, normal_y, normal_z),
        })
    }

    let number_of_triangles = file.read_u32::<LittleEndian>().unwrap() / 3;
    for _ in 0..number_of_triangles {
        let first = file.read_u16::<LittleEndian>().unwrap();
        let second = file.read_u16::<LittleEndian>().unwrap();
        let third = file.read_u16::<LittleEndian>().unwrap();
        model.triangles.push(Triangle(first, second, third));
    }
    let mut padding = [0u8; 13];
    file.read_exact(&mut padding).unwrap();

    let mut end_file_tag = [0u8; 4];
    file.read_exact(&mut end_file_tag).unwrap();
    let end_file_tag = str::from_utf8(&end_file_tag).unwrap();
    if end_file_tag != "EHSM" {
        panic!("Expexted EHSM, but found {}", end_file_tag);
    }

    model
}
