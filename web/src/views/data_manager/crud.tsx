import * as api from './api';
import {
    UserPageQuery,
    AddReq,
    DelReq,
    EditReq,
    CreateCrudOptionsProps,
    CreateCrudOptionsRet,
    dict
} from '@fast-crud/fast-crud';
import { commonCrudConfig } from "/@/utils/commonCrud";

export const createCrudOptions = function ({
    crudExpose
}: CreateCrudOptionsProps): CreateCrudOptionsRet {
    // 定义API请求函数
    const pageRequest = async (query: UserPageQuery) => {
        return await api.GetList(query);
    };
    const editRequest = async ({form, row}: EditReq) => {
        form.id = row.id;
        return await api.UpdateObj(form);
    };
    const delRequest = async ({row}: DelReq) => {
        return await api.DelObj(row.id);
    };
    const addRequest = async ({form}: AddReq) => {
        try {
            if (!form.data) {
                throw new Error('请选择要上传的文件');
            }

            console.log('开始处理文件上传，form.data:', form.data);
            const fileData = form.data;
            const formData = new FormData();

            // 添加基本字段到formData
            formData.append('name', form.name || '');
            formData.append('description', form.description || '');
            formData.append('type', form.type || '');


            if (typeof fileData === 'string') {
                // 如果是字符串路径，需要去除可能的前导斜杠
                const cleanPath = fileData.replace(/^\/+/, '');
                console.log('使用文件路径上传:', cleanPath);
                formData.append('data', cleanPath);
            } else {
                // 如果是文件对象，尝试获取File对象
                const getValue = (obj: any): File | null => {
                    if (obj instanceof File) return obj;
                    if (obj?.raw instanceof File) return obj.raw;
                    if (obj?.originFileObj instanceof File) return obj.originFileObj;
                    if (Array.isArray(obj) && obj.length > 0) return getValue(obj[0]);
                    return null;
                };

                const file = getValue(fileData);
                if (!file) {
                    throw new Error('无法获取有效的文件对象');
                }
                console.log('使用File对象上传:', file.name);
                formData.append('data', file);
            }

            // 显示formData内容用于调试
            console.log('FormData内容:');
            for (const pair of formData.entries()) {
                console.log(pair[0] + ': ' + pair[1]);
            }

            // 上传文件和其他字段
            console.log('开始上传数据...');
            const uploadRes = await api.UploadDataset(formData);
            console.log('上传响应:', uploadRes);

            if (!uploadRes.data) {
                throw new Error('上传失败: 未收到响应数据');
            }

            // 数据集记录应该已经在后端创建，这里直接返回响应
            return uploadRes;
        } catch (error: any) {
            console.error('处理错误:', error);
            throw new Error(error.message || '添加数据集失败');
        }
    };
    // 定义字段配置
    const baseConfig = {
        create_datetime: { form: false, table: false, search: false },
        update_datetime: { form: false, table: false, search: false },
        creator_name: { form: false, table: false, search: false },
        modifier_name: { form: false, table: false, search: false },
        dept_belong_id: { form: false, table: false, search: false },
        description: { form: true, table: true, search: false }
    };

    // 应用通用配置
    const commonConfig = commonCrudConfig(baseConfig);
    
    return {
        crudOptions: {
            request: {
                pageRequest,
                addRequest,
                editRequest,
                delRequest,
            },
            pageOptions: {
                compact: true
            },
            options: {
                tableType: "vxe-table",
                rowKey: true,
                rowId: "id",
                height: "100%",
                highlightCurrentRow: false
            },
            actionbar: {
                buttons: {
                    add: {
                        show: true
                    }
                }
            },
            rowHandle: {
                fixed: 'right',
                width: 140,
                buttons: {
                    view: {
                        iconRight: 'View',
                        show: true, // 显示查看按钮
                        text: "查看"
                    },
                    edit: {
                        iconRight: 'Edit',
                        show: true, // 显示编辑按钮
                        text: "编辑"
                    },
                    remove: {
                        iconRight: 'Delete',
                        show: true, // 显示删除按钮
                        text: "删除"
                    }
                }
            },
            columns: {
                ...commonConfig,
                name: {
                    title: "数据集名称",
                    key: "name",
                    sortable: true,
                    treeNode: true,
                    type: "input",
                    form: {
                        rules: [
                            { required: true, message: "数据集名称必填" }
                        ],
                        component: {
                            props: {
                                clearable: true
                            },
                            placeholder: "请输入数据集名称"
                        }
                    }
                },
                type: {
                    title: "数据集类型",
                    key: "type",
                    sortable: true,
                    type: "input",
                    form: {
                        component: {
                            props: {
                                clearable: true
                            },
                            placeholder: "请输入数据集类型"
                        }
                    }
                },
                data: {
                    title: "数据集文件",
                    key: "data",
                    type: "file-uploader",
                    form: {
                        rules: [{ required: true, message: "请上传数据集文件" }],
                        component: {
                            name: "fs-file-uploader",
                            props: {
                                btnText: "选择文件",
                                limit: 1,
                                accept: ".png,.jpg,.jpeg,.bmp,.zip",
                                drag: true,
                                immediate: false, // 禁止自动上传
                                onSuccess: (res: any, file: any) => {
                                    console.log('上传成功，响应:', res);
                                    console.log('上传成功，文件对象:', file);
                                    return file;
                                },
                                onChange: (file: any) => {
                                    console.log('文件改变，原始文件对象:', file);
                                    if (file instanceof File) {
                                        return file;
                                    } else if (file?.raw instanceof File) {
                                        return file.raw;
                                    }
                                    return null;
                                }
                            }
                        },
                        helper: "支持图片格式(png/jpg/jpeg/bmp)及zip压缩包",
                        on: {
                            change: (ctx: any) => {
                                console.log('文件变化事件:', ctx);
                                console.log('当前文件值:', ctx.value);
                                if (ctx.value) {
                                    // 检查文件对象结构
                                    console.log('文件对象结构:', {
                                        isArray: Array.isArray(ctx.value),
                                        hasRaw: ctx.value.raw || (Array.isArray(ctx.value) && ctx.value[0]?.raw),
                                        type: typeof ctx.value
                                    });
                                }
                            }
                        }
                    }
                },
                ...commonConfig
            }
        }
    };
};