use eframe::{
    egui::{self, WidgetText},
    emath,
};

use sia_parser::types::{SiaVector2, SiaVector3};

pub fn numeric_helper<Num>(ui: &mut egui::Ui, label: impl Into<WidgetText>, value: &mut Num)
where
    Num: emath::Numeric,
{
    ui.horizontal(|ui| {
        ui.label(label);
        ui.add(egui::DragValue::new(value));
    });
}

pub fn text_edit_helper<S>(ui: &mut egui::Ui, label: impl Into<WidgetText>, value: &mut S)
where
    S: egui::widgets::text_edit::TextBuffer,
{
    ui.horizontal(|ui| {
        ui.label(label);
        ui.text_edit_singleline(value);
    });
}

pub fn byte_array_helper(ui: &mut egui::Ui, header: impl Into<WidgetText>, array: &mut [u8]) {
    if array.is_empty() {
        return;
    }
    ui.collapsing(header, |ui| {
        ui.horizontal_wrapped(|ui| {
            for byte in array {
                ui.add(egui::DragValue::new(byte));
            }
        });
    });
}

pub fn vector3_helper(ui: &mut egui::Ui, label: impl Into<WidgetText>, value: &mut SiaVector3) {
    ui.collapsing(label, |ui| {
        ui.horizontal(|ui| {
            ui.label("x");
            ui.add(egui::DragValue::new(&mut value.x).speed(0.01));
        });
        ui.horizontal(|ui| {
            ui.label("y");
            ui.add(egui::DragValue::new(&mut value.y).speed(0.01));
        });
        ui.horizontal(|ui| {
            ui.label("z");
            ui.add(egui::DragValue::new(&mut value.z).speed(0.01));
        });
    });
}

pub fn vector2_helper(ui: &mut egui::Ui, label: impl Into<WidgetText>, value: &mut SiaVector2) {
    ui.collapsing(label, |ui| {
        ui.horizontal(|ui| {
            ui.label("x");
            ui.add(egui::DragValue::new(&mut value.x).speed(0.01));
        });
        ui.horizontal(|ui| {
            ui.label("y");
            ui.add(egui::DragValue::new(&mut value.y).speed(0.01));
        });
    });
}
