// #![feature(get_mut_unchecked)]

use kiss3d::light::Light;
use kiss3d::resource::{Mesh, TextureManager, TextureWrapping};
use kiss3d::{camera::ArcBall, event::WindowEvent, window::Window};
use nalgebra::{Point2, Point3, Vector3};
use native_dialog::*;
use nfd2::Response;
use std::{cell::RefCell, path::PathBuf, rc::Rc};

mod save_obj;

struct Options {
    wireframe: bool,
}

impl Options {
    fn new() -> Self {
        Options { wireframe: false }
    }
}

fn show_error_dialog(title: &str, text: &str) {
    let _ = MessageAlert {
        title,
        text,
        typ: MessageType::Error,
    }
    .show();
}

fn show_info_dialog(title: &str, text: &str) {
    let _ = MessageAlert {
        title,
        text,
        typ: MessageType::Info,
    }
    .show();
}

fn main() {
    let mut window = Window::new("Football Manager Model Viewer");
    let mut scene_nodes = Vec::new();
    let mut options = Options::new();

    window.set_light(Light::StickToCamera);
    let mut camera = ArcBall::new(Point3::new(0.0f32, 10.0, -10.0), Point3::origin());
    camera.rebind_drag_button(Some(kiss3d::event::MouseButton::Button3));

    let mut texture_manager = TextureManager::new();
    let mut texture_dir: Option<PathBuf> = None;

    let mut model = None;

    match nfd2::open_file_dialog(None, None).expect("Couldn't open file") {
        Response::Okay(filepath) => {
            if filepath.extension().unwrap() == "sia" {
                model = Some(sia_parser::from_path(filepath));
                match model.as_ref().unwrap() {
                    Ok(model) => {
                        show_info_dialog(
                            "Texture Folder",
                            "Please select simatchviewer-pc folder for texture support",
                        );
                        if let Ok(Response::Okay(folder)) = nfd2::open_pick_folder(None) {
                            texture_dir = Some(folder);
                        }

                        for mesh in model.meshes.values().collect::<Vec<_>>() {
                            let mut coords = Vec::new();
                            let mut normals = Vec::new();
                            let mut triangles: Vec<Point3<u16>> = Vec::new();
                            let mut uvs = Vec::new();

                            for vertex in &mesh.vertices {
                                coords.push(Point3::from(vertex.position));
                                normals.push(Vector3::from(vertex.normals));
                                uvs.push(Point2::from(vertex.uv));
                            }

                            for triangle in &mesh.triangles {
                                triangles.push(Point3::new(
                                    triangle.0 as u16,
                                    triangle.1 as u16,
                                    triangle.2 as u16,
                                ));
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
                                if let Some(material) = mesh.materials.get(0) {
                                    if let Some(diffuse) = material.textures.get(0) {
                                        let diffuse_relative_path = &diffuse.name;
                                        let mut diffuse_absolute_path =
                                            texture_dir.join(diffuse_relative_path);
                                        diffuse_absolute_path.set_extension("dds");

                                        if let Ok(texture) = image::open(diffuse_absolute_path) {
                                            let texture_resource = texture_manager
                                                .add_image(texture, diffuse_relative_path);

                                            c.set_texture(texture_resource);
                                        }
                                    }
                                }
                            }

                            scene_nodes.push(c);
                        }
                    }
                    Err(e) => {
                        eprintln!("Error: {}", e);
                        std::process::exit(1)
                    }
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
                        if let Some(Ok(model)) = &model {
                            save_obj::save_as_obj(&model, &texture_dir);
                        }
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
