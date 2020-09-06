#![feature(get_mut_unchecked)]

use kiss3d::light::Light;
use kiss3d::resource::{Mesh, TextureManager, TextureWrapping};
use kiss3d::{camera::ArcBall, event::WindowEvent, window::Window};
use nalgebra::{Point2, Point3, Vector3};
use native_dialog::*;
use nfd2::Response;
use std::{cell::RefCell, path::PathBuf, rc::Rc};

use obj_exporter;
use obj_exporter::{Geometry, ObjSet, Object, Primitive, Shape, TVertex, Vertex};

struct Options {
    wireframe: bool,
}

impl Options {
    fn new() -> Self {
        Options { wireframe: false }
    }
}

fn main() {
    let mut window = Window::new("Football Manager Model Viewer");
    let mut scene_nodes = Vec::new();
    let mut options = Options::new();

    window.set_light(Light::StickToCamera);
    let mut camera = ArcBall::new(Point3::new(0.0f32, 10.0, -10.0), Point3::origin());
    camera.rebind_drag_button(Some(kiss3d::event::MouseButton::Button3));

    let mut texture_manager = TextureManager::new();

    let mut model = None;

    match nfd2::open_file_dialog(None, None).expect("Couldn't open file") {
        Response::Okay(filepath) => {
            let dialog = MessageAlert {
                title: "Texture Folder",
                text: "Please select simatchviewer-pc folder for texture support",
                typ: MessageType::Info,
            };
            dialog.show().unwrap();
            let mut texture_dir: Option<PathBuf> = None;
            if let Ok(Response::Okay(folder)) = nfd2::open_pick_folder(None) {
                texture_dir = Some(folder);
            }
            if filepath.extension().unwrap() == "sia" {
                model = Some(sia_parser::parse(filepath));
                let model = model.as_ref().unwrap();

                for mesh in &model.meshes {
                    let mut coords = Vec::new();
                    let mut normals = Vec::new();
                    let mut triangles = Vec::new();
                    let mut uvs = Vec::new();

                    for vertex in &mesh.vertices {
                        coords.push(Point3::from(vertex.position));
                        normals.push(Vector3::from(vertex.normals));
                        uvs.push(Point2::from(vertex.uv));
                    }

                    for triangle in &mesh.triangles {
                        triangles.push(Point3::new(triangle.0, triangle.1, triangle.2));
                    }

                    let mut c = window.add_mesh(
                        Rc::new(RefCell::new(Mesh::new(
                            coords,
                            triangles,
                            Some(normals),
                            Some(uvs),
                            false,
                        ))),
                        Vector3::new(1.0, 1.0, 1.0),
                    );
                    c.reorient(
                        &Point3::new(0.0, 0.0, 0.0),
                        &Point3::new(0.0, 1.0, 0.0),
                        &Vector3::new(1.0, 0.0, 0.0),
                    );
                    c.enable_backface_culling(true);

                    if let Some(texture_dir) = &texture_dir {
                        let diffuse_relative_path = &mesh.materials[0].textures[0].name;
                        let mut diffuse_absolute_path = texture_dir.join(diffuse_relative_path);
                        diffuse_absolute_path.set_extension("dds");

                        if let Ok(texture) = image::open(diffuse_absolute_path) {
                            let mut texture_resource =
                                texture_manager.add_image(texture, diffuse_relative_path);

                            unsafe {
                                let text = Rc::get_mut_unchecked(&mut texture_resource);
                                text.set_wrapping_s(TextureWrapping::Repeat);
                                text.set_wrapping_t(TextureWrapping::Repeat);
                            }
                            c.set_texture(texture_resource);
                        }
                    }

                    scene_nodes.push(c);
                }
            }
        }
        _ => {}
    }

    while window.render_with_camera(&mut camera) {
        for mut event in window.events().iter() {
            match event.value {
                WindowEvent::Key(kiss3d::event::Key::S, kiss3d::event::Action::Press, modifers) => {
                    if modifers.contains(kiss3d::event::Modifiers::Control) {
                        let mut objects = Vec::new();
                        for mesh in &model.as_ref().unwrap().meshes {
                            for material in &mesh.materials {
                                for texture in &material.textures {
                                    dbg!(&texture);
                                }
                            }
                        }
                        for mesh in &model.as_ref().unwrap().meshes {
                            let object = Object {
                                name: model.as_ref().unwrap().name.to_owned(),
                                vertices: mesh
                                    .vertices
                                    .iter()
                                    .map(|v| v.position)
                                    .map(|v| Vertex {
                                        x: v.x.into(),
                                        y: v.y.into(),
                                        z: v.z.into(),
                                    })
                                    .collect(),
                                tex_vertices: mesh
                                    .vertices
                                    .iter()
                                    .map(|v| v.uv)
                                    .map(|uv| TVertex {
                                        u: uv.x.into(),
                                        v: (uv.y - 1f32).abs().into(),
                                        w: 0.0,
                                    })
                                    .collect(),
                                normals: vec![],
                                geometry: vec![Geometry {
                                    material_name: Some(model.as_ref().unwrap().name.to_owned()),
                                    shapes: mesh
                                        .triangles
                                        .iter()
                                        .map(|t| Shape {
                                            primitive: Primitive::Triangle(
                                                (t.0.into(), Some(t.0.into()), None),
                                                (t.1.into(), Some(t.1.into()), None),
                                                (t.2.into(), Some(t.2.into()), None),
                                            ),
                                            groups: vec![],
                                            smoothing_groups: vec![0],
                                        })
                                        .collect(),
                                }],
                            };
                            objects.push(object);
                        }
                        let set = ObjSet {
                            material_library: None,
                            objects,
                        };

                        obj_exporter::export_to_file(
                            &set,
                            format!("{}{}", model.as_ref().unwrap().name, ".obj"),
                        )
                        .unwrap();
                    }
                }
                WindowEvent::Key(kiss3d::event::Key::W, kiss3d::event::Action::Press, modifers) => {
                    if modifers.contains(kiss3d::event::Modifiers::Shift) {
                        if options.wireframe {
                            for node in &mut scene_nodes {
                                node.set_points_size(0.0);
                                node.set_lines_width(0.0);
                                node.set_surface_rendering_activation(true);
                            }
                            options.wireframe = false;
                        } else {
                            for node in &mut scene_nodes {
                                node.set_points_size(4.0);
                                node.set_lines_width(1.0);
                                node.set_surface_rendering_activation(false);
                            }
                            options.wireframe = true;
                        }
                    }
                }
                WindowEvent::Scroll(_, y_shift, _) => {
                    camera.set_dist(camera.dist() - (y_shift as f32) * 0.1);
                    event.inhibited = true
                }
                _ => {}
            }
        }
    }
}
