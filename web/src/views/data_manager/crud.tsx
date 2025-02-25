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

            // 修改文件对象获取逻辑
            let fileToUpload;
            if (Array.isArray(form.data)) {
                fileToUpload = form.data[0]?.response || form.data[0]?.raw || form.data[0];
            } else {
                fileToUpload = form.data.response || form.data.raw || form.data;
            }

            console.log('文件对象:', fileToUpload);  // 调试日志

            // 构建FormData
            const formData = new FormData();
            formData.append('data', fileToUpload);

            // 上传文件
            const uploadRes = await api.UploadDataset(formData);

            if (uploadRes.data && uploadRes.data.filename) {
                form.file_name = uploadRes.data.filename;
            } else {
                throw new Error('文件上传失败: 未收到文件名');
            }

            // 创建数据集记录
            return await api.AddObj({
                name: form.name,
                description: form.description,
                type: form.type,
                file_name: form.file_name
            });
        } catch (error: any) {
            console.error('处理错误:', error);
            throw new Error(error.message || '添加数据集失败');
        }
    };
    
    // 获取公共配置
    const commonConfig = commonCrudConfig({
        create_datetime: { form: true, table: true, search: true },
        update_datetime: { form: true, table: true, search: true },
        creator_name: { form: true, table: true, search: true },
        modifier_name: { form: true, table: true, search: true },
        dept_belong_id: { form: true, table: true, search: true },
        description: { form: false, table: false, search: false } // 不使用公共的description配置
    });
    
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
                        type: 'text',
                        thin: true,
                        show: true, // 显示查看按钮
                        text: "查看"
                    },
                    edit: {
                        type: 'text',
                        thin: true,
                        show: true, // 显示编辑按钮
                        text: "编辑"
                    },
                    remove: {
                        type: 'text',
                        thin: true,
                        show: true, // 显示删除按钮
                        text: "删除"
                    }
                }
            },
            columns: {
                _index: {
                    title: "序号",
                    type: "index",
                    form: {show: false},
                    column: {
                        align: "center",
                        width: "70px",
                        columnSetDisabled: true, //禁止在列设置中选择
                    }
                },
                id: {
                    title: "ID",
                    key: "id",
                    show: false,
                    disabled: true,
                    width: 90,
                    form: {
                        disabled: true
                    }
                },
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
                dataset_description: {
                    title: "数据集描述",
                    key: "description", 
                    type: "textarea",
                    form: {
                        component: {
                            props: {
                                clearable: true
                            },
                            placeholder: "请输入数据集描述"
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
                    },
                    search: {
                        component: {
                            props: {
                                clearable: true
                            }
                        }
                    }
                },
                create_time: {
                    title: "创建时间",
                    key: "create_time",
                    type: "datetime",
                    sortable: true,
                    form: {
                        disabled: true
                    }
                },
                update_time: {
                    title: "更新时间",
                    key: "update_time",
                    type: "datetime",
                    sortable: true,
                    form: {
                        disabled: true
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
                                onSuccess: (res: any) => {
                                    console.log('上传成功:', res);
                                    // 直接返回文件对象
                                    return res.data || res;
                                }
                            }
                        },
                        helper: "支持图片格式(png/jpg/jpeg/bmp)及zip压缩包",
                        on: {
                            change: (ctx: any) => {
                                console.log('文件变化:', ctx);
                            }
                        }
                    }
                },
                ...commonConfig
            }
        }
    };
};