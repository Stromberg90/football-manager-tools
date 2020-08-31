use kiss3d::light::Light;
use kiss3d::resource::Mesh;
use kiss3d::scene::SceneNode;
use kiss3d::{camera::ArcBall, event::WindowEvent, window::Window};
use nalgebra::{Point2, Point3, Vector3};
use nfd2::Response;
use std::{cell::RefCell, rc::Rc};

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

    match nfd2::open_file_dialog(None, None).expect("Couldn't open file") {
        Response::Okay(filepath) => {
            if filepath.extension().unwrap() == "sia" {
                let model = sia_parser::parse(filepath);

                for mesh in model.meshes {
                    let mut coords = Vec::new();
                    let mut normals = Vec::new();
                    let mut triangles = Vec::new();
                    let mut uvs = Vec::new();

                    for vertex in mesh.vertices {
                        coords.push(Point3::from(vertex.position));
                        normals.push(Vector3::from(vertex.normals));
                        uvs.push(Point2::from(vertex.uv));
                    }

                    for triangle in mesh.triangles {
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

                    scene_nodes.push(c);
                }
            }
        }
        _ => {}
    }

    while window.render_with_camera(&mut camera) {
        for mut event in window.events().iter() {
            match event.value {
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
