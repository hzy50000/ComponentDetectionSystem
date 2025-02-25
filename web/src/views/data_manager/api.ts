import { request } from "/@/utils/service";
import { UserPageQuery, AddReq, EditReq } from '@fast-crud/fast-crud';
import { Session } from '/@/utils/storage';

export const urlPrefix = '/api/datasetManager/';

export function UploadDataset(data: FormData) {
    const token = Session.get('token');
    return request({
        url: `${urlPrefix}upload_dataset/`,
        method: 'post',
        headers: {
            'Authorization': `JWT ${token}`
        },
        data: data,
        // 重要：确保axios不会处理FormData
        transformRequest: [(data: any) => data]
    });
}

export function GetList(query: UserPageQuery) {
    return request({
        url: urlPrefix,
        method: 'get',
        params: query
    });
}

export function AddObj(obj: AddReq) {
    return request({
        url: urlPrefix,
        method: 'post',
        data: obj
    });
}

export function UpdateObj(obj: EditReq) {
    return request({
        url: urlPrefix,
        method: 'put',
        data: obj
    });
}

export function DelObj(id: string | number) {
    // 移除URL中可能的双斜杠问题
    return request({
        url: `${urlPrefix}${id}`,
        method: 'delete',
        data: { id }
    });
}