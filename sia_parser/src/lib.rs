use byteorder::{LittleEndian, ReadBytesExt};
use nalgebra::{Vector2, Vector3};
use std::fs::File;
use std::io::Seek;
use std::io::{self, Read, SeekFrom, Write};
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
    pub name: String,
    pub id: u8,
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
    pub num_vertices: u32,
    pub num_triangles: u32,
    pub id: u32,
    pub materials_num: u8,
    pub materials: Vec<Material>,
    pub vertices: Vec<Vertex>,
    pub triangles: Vec<Triangle>,
}

impl Mesh {
    fn new() -> Self {
        Mesh {
            num_vertices: 0,
            num_triangles: 0,
            id: 0,
            materials_num: 0,
            materials: Vec::new(),
            vertices: Vec::new(),
            triangles: Vec::new(),
        }
    }
}

#[derive(Debug)]
pub struct Model {
    pub who_knows: f32,
    pub objects_num: u32,
    pub object_id: u32,
    pub something_about_faces_or_vertices: u32,
    pub maybe_version: u32,
    pub name: String,
    pub bounding_box: BoundingBox,
    pub num_vertices: u32,
    pub num_meshes: u32,
    pub meshes: Vec<Mesh>,
}

impl Model {
    fn new() -> Self {
        Model {
            who_knows: 0f32,
            objects_num: 0,
            object_id: 0,
            something_about_faces_or_vertices: 0,
            maybe_version: 0,
            name: String::new(),
            bounding_box: BoundingBox::new(),
            num_vertices: 0,
            num_meshes: 0,
            meshes: Vec::new(),
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

fn read_bounding_box(file: &mut File) -> BoundingBox {
    BoundingBox {
        min_x: file.read_f32::<LittleEndian>().unwrap(),
        min_y: file.read_f32::<LittleEndian>().unwrap(),
        min_z: file.read_f32::<LittleEndian>().unwrap(),
        max_x: file.read_f32::<LittleEndian>().unwrap(),
        max_y: file.read_f32::<LittleEndian>().unwrap(),
        max_z: file.read_f32::<LittleEndian>().unwrap(),
    }
}

fn read_vector3(file: &mut File) -> Vector3<f32> {
    let x = file.read_f32::<LittleEndian>().unwrap();
    let y = file.read_f32::<LittleEndian>().unwrap();
    let z = file.read_f32::<LittleEndian>().unwrap();
    Vector3::new(x, y, z)
}

fn read_vector2(file: &mut File) -> Vector2<f32> {
    let x = file.read_f32::<LittleEndian>().unwrap();
    let y = file.read_f32::<LittleEndian>().unwrap();
    Vector2::new(x, y)
}

fn read_triangle(file: &mut File) -> Triangle {
    Triangle(
        file.read_u16::<LittleEndian>().unwrap(),
        file.read_u16::<LittleEndian>().unwrap(),
        file.read_u16::<LittleEndian>().unwrap(),
    )
}

trait Skip {
    fn skip(&mut self, num_bytes: i64);
}

impl Skip for File {
    fn skip(&mut self, num_bytes: i64) {
        self.seek(SeekFrom::Current(num_bytes)).unwrap();
    }
}

trait Position {
    fn position(&mut self) -> io::Result<u64>;
}

impl Position for File {
    fn position(&mut self) -> Result<u64, std::io::Error> {
        self.seek(SeekFrom::Current(0))
    }
}

pub fn parse<P: AsRef<Path>>(filepath: P) -> Model {
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
    file.skip(12);

    // This might be some sort of scale, since it tends to resemble another bouding box value
    // changing it did nothing
    model.who_knows = file.read_f32::<LittleEndian>().unwrap();

    model.bounding_box = read_bounding_box(&mut file);

    model.objects_num = file.read_u32::<LittleEndian>().unwrap();

    for _ in 0..model.objects_num {
        let mut mesh = Mesh::new();
        file.read_u32::<LittleEndian>().unwrap();

        // Vertices
        mesh.num_vertices = file.read_u32::<LittleEndian>().unwrap();

        file.read_u32::<LittleEndian>().unwrap();

        // Number of triangles when divided by 3
        mesh.num_triangles = file.read_u32::<LittleEndian>().unwrap() / 3;

        // ID
        mesh.id = file.read_u32::<LittleEndian>().unwrap();
        file.skip(8);
        model.meshes.push(mesh);
    }

    model.num_meshes = file.read_u32::<LittleEndian>().unwrap();

    // Changing these did nothing
    file.skip(16);

    for i in 0..model.num_meshes {
        let mut mesh = model.meshes.get_mut(i as usize).unwrap();
        let material_kind = read_string(&mut file);
        mesh.materials_num = file.read_u8().unwrap();
        for _ in 0..mesh.materials_num {
            let mut material = Material::new();
            material.kind = material_kind.to_owned();
            material.name = read_string(&mut file);
            material.textures_num = file.read_u8().unwrap();
            for _ in 0..material.textures_num {
                let texture_id = file.read_u8().unwrap(); //Maybe a way to identify which texture it is, like a id
                let texture = Texture {
                    name: read_string(&mut file),
                    id: texture_id,
                };
                material.textures.push(texture);
            }
            mesh.materials.push(material);
        }
        if i != model.num_meshes - 1 {
            file.skip(80);
        }
    }
    file.skip(64);

    // Maybe this is for this mesh, and the earlier one is for the entire file.
    let local_num_vertecies = file.read_u32::<LittleEndian>();

    let _maybe_a_identifer_num = file.read_u32::<LittleEndian>();

    for i in 0..model.num_meshes {
        let mesh = model.meshes.get_mut(i as usize).unwrap();

        for _ in 0..mesh.num_vertices {
            let pos = read_vector3(&mut file);

            // Think these are normals, when plotted out as vertices, they make a sphere.
            // Which makes sense if it's normals
            // Actually, I'm second guessing myself
            let normal = read_vector3(&mut file);

            let uv = read_vector2(&mut file);

            // println!("Unknowns");
            // Thinking these are tangents or binormals, last one is always 1 or -1
            file.skip(16);

            mesh.vertices.push(Vertex {
                position: pos,
                uv,
                normals: normal,
            })
        }
    }

    let number_of_triangles = file.read_u32::<LittleEndian>().unwrap() / 3;

    for i in 0..model.num_meshes {
        let mesh = model.meshes.get_mut(i as usize).unwrap();
        for _ in 0..mesh.num_triangles {
            mesh.triangles.push(read_triangle(&mut file));
        }
    }
    file.skip(13);

    let mut end_file_tag = [0u8; 4];
    file.read_exact(&mut end_file_tag).unwrap();
    return model;
    let end_file_tag = str::from_utf8(&end_file_tag).unwrap();
    if end_file_tag != "EHSM" {
        panic!("Expexted EHSM, but found {}", end_file_tag);
    }

    model
}
