use std::collections::HashMap;

use pyo3::{
    types::{self, PyUnicode},
    PyAny,
};

use crate::bounding_box::BoundingBox;
use crate::mesh::Mesh;

#[derive(Debug)]
pub enum EndKind {
    MeshType(String),
    IsBanner(bool),
    IsCompBanner(bool),
}

impl From<&PyAny> for EndKind {
    fn from(item: &PyAny) -> Self {
        let end_kind_type: u8 = item
            .getattr("type")
            .unwrap()
            .getattr("value")
            .unwrap()
            .extract()
            .unwrap();
        if end_kind_type == 0 {
            EndKind::MeshType(
                PyUnicode::from_object(item.getattr("value").unwrap(), "utf-8", "")
                    .unwrap()
                    .to_string(),
            )
        } else if end_kind_type == 1 {
            EndKind::IsBanner(item.getattr("value").unwrap().extract().unwrap())
        } else if end_kind_type == 2 {
            EndKind::IsCompBanner(item.getattr("value").unwrap().extract().unwrap())
        } else {
            panic!("Unknown EndKind");
        }
    }
}

#[derive(Debug, Default)]
pub struct Model {
    pub objects_num: u32,
    pub object_id: u32,
    pub something_about_faces_or_vertices: u32,
    pub name: String,
    pub bounding_box: BoundingBox,
    pub num_vertices: u32,
    pub num_meshes: u32,
    pub meshes: HashMap<usize, Mesh>,
    pub end_kind: Option<EndKind>,
}

impl Model {
    pub(crate) fn new() -> Self {
        Model {
            objects_num: 0,
            object_id: 0,
            something_about_faces_or_vertices: 0,
            name: String::new(),
            bounding_box: BoundingBox::new(),
            num_vertices: 0,
            num_meshes: 0,
            meshes: HashMap::new(), // I'm using this instead of a vec, cause I need to make sure that the indecies match
            end_kind: None,
        }
    }
}

impl From<&PyAny> for Model {
    fn from(item: &PyAny) -> Self {
        let mut model = Model::new();
        model.name = PyUnicode::from_object(item.getattr("name").unwrap(), "utf-8", "")
            .unwrap()
            .to_string();
        model.bounding_box = item.getattr("bounding_box").unwrap().into();
        for (index, mesh) in item
            .getattr("meshes")
            .unwrap()
            .cast_as::<types::PyDict>()
            .unwrap()
        {
            model.meshes.insert(index.extract().unwrap(), mesh.into());
        }
        if item.hasattr("end_kind").unwrap() {
            model.end_kind = Some(item.getattr("end_kind").unwrap().into());
        }
        model
    }
}
