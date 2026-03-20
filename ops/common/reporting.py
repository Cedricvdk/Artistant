def report_error(operator, message):
    operator.report({'ERROR'}, message)
    return {'CANCELLED'}


def report_info(operator, message):
    operator.report({'INFO'}, message)
    return {'FINISHED'}
